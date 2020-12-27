import re
import ssl
import sys
import socket
import websocket
import telnetlib

from time import time
from socket import timeout as Timeout, error as SocketError

def Bytes(s):
    if isinstance(s, str): return s.encode("ascii")
    assert isinstance(s, bytes)
    return s

def Str(s):
    if isinstance(s, bytes): return s.decode("ascii")
    assert isinstance(s, str)
    return s

__all__ = "Sock Sock6 toSock SockU SockU6 toSockU Timeout SocketError".split()

DEFAULT_TIMEOUT = 30
PORT_REGEXP = re.compile(r"(:| |;|/|\|)+(?P<port>\d+)$")

'''
TODO:
- tests
- check Sock6/toSock6
- read_until(_re) accept list also
- think about losing socket data on EOFError
- quick fail mode? if exploit fails, read_until("$ ") will wait the whole timeout;
'''


def parse_addr(addr, port=None):
    """
    If port is embedded in addr string, it should be delimited with one or more of:
        " :;|/"

    Examples:
        parse_addr("localhost", 3123)
        parse_addr(("localhost", 3123))
        parse_addr("127.0.0.1:3123")
        parse_addr("127.0.0.1: 3123")
        parse_addr("127.0.0.1|3123")
        parse_addr("127.0.0.1/3123")
        parse_addr("127.0.0.1 3123")
        parse_addr("example.com:3123")
        parse_addr("example.com:| /3123")
    """
    _host = None
    _port = None

    if port is not None:
        _host = addr
        _port = int(port)

    elif isinstance(addr, tuple):
        _host = addr[0]
        _port = int(addr[1])

    elif isinstance(addr, str):
        if addr.startswith("ws://") or addr.startswith("wss://"):
            return addr

        match = PORT_REGEXP.search(addr.strip())
        if match:
            _host = addr[:match.start()]
            _port = int(match.group("port"))

    if _host is None or _port is None:
        raise TypeError("Can't understand address: addr=%s, port=%s" % (addr, port))

    if not isinstance(_host, str):
        raise TypeError("Host should be string")

    # strip IPv6 brackets
    _host = _host.strip("[]")
    return _host, _port


class AbstractSock(object):
    """
    SomeSock("127.0.0.1", 3123, timeout=15)
    - timeout should be given using explicit keyword
    """

    SOCKET_FAMILY = NotImplemented
    SOCKET_TYPE = NotImplemented
    RECV_SIZE = 4096

    def __init__(self, *addr, **timeout_dict):
        self.addr = parse_addr(*addr)

        # python2 does not allow (*args, timeout=None) :(
        self.timeout = float(timeout_dict.pop("timeout", DEFAULT_TIMEOUT))
        if timeout_dict:
            raise TypeError("Only timeout should be given through keyword args")

        self.buf = b""
        self.eof = False

        self._init_sock()
        self._connect()
        return

    @classmethod
    def from_socket(cls, sock, timeout=None):
        self = object.__new__(cls)
        self.addr = sock.getpeername()
        self.sock = sock

        assert self.SOCKET_TYPE == sock.type

        if timeout is not None:
            self.timeout = float(timeout)
            self.sock.settimeout(self.timeout)
        else:
            self.timeout = self.sock.gettimeout()

        self.buf = b""
        self.eof = False
        return self

    def _init_sock(self):
        self.sock = socket.socket(self.SOCKET_FAMILY, self.SOCKET_TYPE)
        self.sock.settimeout(self.timeout)

    def _connect(self):
        return NotImplemented

    def recv(self):
        return NotImplemented

    def send(self):
        return NotImplemented

    def send_line(self, line):
        return self.send(Bytes(line) + b"\n")

    def read_line(self, timeout=None):
        return self.read_until(b"\n", timeout=timeout)

    def read_one(self, timeout=None):
        """
        Read something from socket
        timeout = -1  - wait until something new in socket
        timeout = 0   - return cached buffer + socket buffer immediately
        timeout = N   - wait N seconds until something new in socket, else raise TimeoutError
        """
        self._fill_one(timeout)
        if not self.buf and timeout != 0:
            raise EOFError("Connection closed")
        res = self.buf
        self.buf = b""
        return res

    def read_all(self, timeout=None):
        """
        Read everything from socket (the other side should close socket before timeout)
        """
        self.read_cond(lambda x: x.eof, timeout)
        res = self.buf
        self.buf = b""
        return res

    def skip_until(self, s, timeout=None):
        """
        Skip everything until first occurence of string @s, stop before occurence.
        Return nothing.
        """
        s = Bytes(s)
        self.read_cond(lambda x: s in x.buf, timeout)
        start = self.buf.find(s)
        self.buf = self.buf[start:]
        return

    def skip_until_re(self, r, flags=0, timeout=None):
        """
        Skip everything until first match of regexp @r, stop before match.
        Return match.
        """
        r = Bytes(r)
        match = self.read_cond(
            lambda x: re.search(r, x.buf, flags=flags), timeout)
        self.buf = self.buf[match.start():]
        return match if len(match.groups()) > 1 else match.group(len(match.groups()))

    def read_until(self, s, timeout=None):
        """
        Read everything until first occurence of string @s, stop after occurence.
        Return everything before @s, and @s.
        """
        s = Bytes(s)
        self.read_cond(lambda x: s in x.buf, timeout)
        end = self.buf.find(s) + len(s)
        res = self.buf[:end]
        self.buf = self.buf[end:]
        return res

    def read_until_re(self, r, flags=0, timeout=None):
        """
        Read everything until first match of regexp @r, stop after match.
        Return match.
        Note: if you need the data before match, you can make group (.*?) for that:
            r1 = r"(\d) coins"
            r2 = r"(.*?)(\d coins)"
        """
        r = Bytes(r)
        match = self.read_cond(lambda x: re.search(r, x.buf, flags=flags), timeout)
        self.buf = self.buf[match.end():]
        return match if len(match.groups()) > 1 else match.group(len(match.groups()))

    def read_nbytes(self, n, timeout=None):
        self.read_cond(lambda x: len(x.buf) >= n, timeout)
        self.buf, res = self.buf[n:], self.buf[:n]
        return res

    def read_cond(self, cond, timeout=None):
        """
        Read bytes while @cond(self) is False. Return @cond return.
        self.buf should be analyzed/cropped by caller, if needed
        (this is rather low-level function, helper)
        """
        time_start = time()
        remaining = timeout
        if timeout is None:
            timeout = self.timeout

        if self.eof and not self.buf:
            raise EOFError("Connection closed")

        res = cond(self)

        while not res:
            self._fill_one(remaining)

            res = cond(self)
            if res:
                break

            if self.eof:
                raise EOFError("Connection closed")

            if timeout == -1:
                remaining = -1
            elif timeout == 0:
                raise Timeout("read_cond timeout")
            else:
                remaining = time_start + timeout - time()
                if remaining <= 0:
                    raise Timeout("read_cond timeout")

        return res

    def _fill_one(self, timeout=None):
        """Read something from socket.
        timeout = -1  -  blocking until read
        timeout = 0   -  non-blocking
        timeout = N   -  blocking until read or timeout
        """
        if timeout is None:
            timeout = self.timeout

        if timeout == 0:
            self.sock.setblocking(False)
            try:
                self.buf += self.recv(self.RECV_SIZE)
            except SocketError:
                # WHAT?
                pass
            return

        if timeout == -1:
            self.sock.settimeout(None)  # blocking, infinity timeout
        else:
            self.sock.setblocking(True)  # it's overriden by settimeout, but for clarity
            self.sock.settimeout(timeout)

        buf = self.recv(self.RECV_SIZE)
        self.eof = (not buf)
        self.buf += buf
        return

    @property
    def socket(self):
        return self.sock

    @property
    def fileno(self):
        return self.sock.fileno()

    def write(self, s):
        return self.send(s)

    def shut_wr(self):
        self.sock.shutdown(socket.SHUT_WR)

    def shut_rd(self):
        self.sock.shutdown(socket.SHUT_RD)

    def close(self):
        return self.sock.close()

    def __del__(self):
        self.sock.close()

    def interact_telnet(self):
        sys.stdout.buffer.write(self.buf)
        self.buf = b""

        t = telnetlib.Telnet()
        t.sock = self.sock
        return t.interact()

    def interact(self):
        # copied from Telnetlib with minor fixes
        import selectors
        _TelnetSelector = selectors.SelectSelector

        sys.stdout.buffer.write(self.buf)
        self.buf = b""

        with _TelnetSelector() as selector:
            selector.register(self.sock, selectors.EVENT_READ)
            selector.register(sys.stdin, selectors.EVENT_READ)

            while True:
                for key, events in selector.select():
                    if key.fileobj is self.sock:
                        try:
                            text = self.read_one()
                        except EOFError:
                            print('*** Connection closed by remote host ***')
                            return
                        if text:
                            sys.stdout.buffer.write(text)
                            sys.stdout.flush()
                    elif key.fileobj is sys.stdin:
                        line = sys.stdin.readline()
                        if not line:
                            return
                        self.send(line)

# pwnlib.tubes method name style
class AbstractPwnlibTubes(object):
    def recvall(self, *args, **kwargs):
        return self.read_all(*args, **kwargs)
    
    def recvline(self, *args, **kwargs):
        return self.read_line(*args, **kwargs)

    def recvuntil(self, *args, **kwargs):
        return self.read_until(*args, **kwargs)

    def recvregex(self, *args, **kwargs):
        return self.read_until_re(*args, **kwargs)

    def sendline(self, *args, **kwargs):
        return self.send_line(*args, **kwargs)

    def readall(self, *args, **kwargs):
        return self.recvall(*args, **kwargs)
    
    def readline(self, *args, **kwargs):
        return self.recvline(*args, **kwargs)
    
    def readuntil(self, *args, **kwargs):
        return self.recvuntil(*args, **kwargs)

    def readregex(self, *args, **kwargs):
        return self.recvregex(*args, **kwargs)

    def interactive(self, *args, **kwargs):
        return self.interact(*args, **kwargs)
    

class IPv4Mixin(object):
    SOCKET_FAMILY = socket.AF_INET


class IPv6Mixin(object):
    SOCKET_FAMILY = socket.AF_INET6


class TCPMixIn(object):
    SOCKET_TYPE = socket.SOCK_STREAM

    def _connect(self):
        self.sock.connect(self.addr)

    def recv(self, bufsize):
        return self.sock.recv(bufsize)

    def send(self, s):
        return self.sock.sendall(Bytes(s))

class SSLMixIn(TCPMixIn):
    def _connect(self):
        TCPMixIn._connect(self)
        self.sock = ssl.wrap_socket(self.sock)


class UDPMixIn(object):
    SOCKET_TYPE = socket.SOCK_DGRAM

    def _connect(self):
        pass  # udp doesn't need connect

    def recv(self, bufsize):
        while True:
            data, addr = self.sock.recvfrom(bufsize)
            if addr == self.addr:
                return data
            # TODO: warning about non-matching addr

    def send(self, s):
        return self.sock.sendto(s, self.addr)


class MyWebSocket(websocket.WebSocket):
    def __init__(self, *args, **kwargs):
        self.buf = b''
        super(MyWebSocket, self).__init__(*args, **kwargs)
    
    def setblocking(self, val):
        pass

    def recvbytes(self, bufsize):
        self.buf += self.recv()
        r = self.buf[:bufsize]
        self.buf = self.buf[bufsize:]

        return r


class WebSocketMixIn(object):
    
    SOCKET_TYPE = socket.SOCK_STREAM

    def _init_sock(self):
        self.sock = websocket.create_connection(self.addr, timeout=self.timeout, class_=MyWebSocket)

    def _connect(self):
        pass

    def recv(self, bufsize):
        return self.sock.recvbytes(bufsize)

    def send(self, s):
        return self.sock.send_binary(Bytes(s))


class WebSock(WebSocketMixIn, AbstractSock, AbstractPwnlibTubes):
    pass


class Sock(TCPMixIn, IPv4Mixin, AbstractSock, AbstractPwnlibTubes):
    pass


class Sock6(TCPMixIn, IPv6Mixin, AbstractSock, AbstractPwnlibTubes):
    pass


class SockU(UDPMixIn, IPv4Mixin, AbstractSock, AbstractPwnlibTubes):
    pass


class SockU6(UDPMixIn, IPv6Mixin, AbstractSock, AbstractPwnlibTubes):
    pass


class SSLSock(SSLMixIn, IPv4Mixin, AbstractSock, AbstractPwnlibTubes):
    pass


class SSLSock6(SSLMixIn, IPv6Mixin, AbstractSock, AbstractPwnlibTubes):
    pass

toSock = Sock.from_socket
toSockU = SockU.from_socket
