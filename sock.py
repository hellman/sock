#!/usr/bin/env python
#-*- coding:utf-8 -*-

import re
import socket
from time import time
from socket import timeout as Timeout, error as SocketError

__all__ = "Sock Sock6 toSock Timeout SocketError".split()

DEFAULT_TIMEOUT = 5

class Sock:
    SOCKET_FAMILY = socket.AF_INET
    def __init__(self, ip, port, timeout=None):
        self.addr = (ip, port)
        self.timeout = timeout
        self.buf = ""
        self.eof = False

        self.sock = socket.socket(self.SOCKET_FAMILY, socket.SOCK_STREAM)
        if timeout is None:
            self.timeout = DEFAULT_TIMEOUT
        self.sock.settimeout(timeout)
        self.sock.connect((ip, port))
        return

    def read_one(self, timeout=None):
        self.fill_one(timeout)
        if not self.buf and timeout != 0:
            raise EOFError("Connection closed")
        buf = self.buf
        self.buf = ""
        return buf

    def read_all(self, timeout=None):
        res = self.read_cond(lambda x: x.eof, timeout)
        self.buf = ""
        return res

    def wait_for(self, s, timeout=None):
        """Wait for string in dataflow, DO NOT return data (to avoid splitting data)"""
        self.read_cond(lambda x: s in x.buf, timeout)
        pos = self.buf.find(s)
        self.buf = self.buf[pos:]
        return

    def wait_for_re(self, r, timeout=None):
        """Wait for RE in dataflow, DO NOT return data (to avoid splitting data)"""
        self.read_cond(lambda x: re.search(r, x.buf), timeout)
        s = re.search(r, self.buf).group(0)
        pos = self.buf.find(s)
        self.buf = self.buf[pos:]
        return

    def read_until(self, s, timeout=None):
        res = self.read_cond(lambda x: s in x.buf, timeout)
        pos = res.find(s) + len(s)
        self.buf = self.buf[pos:]
        return res[:pos]

    def read_until_re(self, r, timeout=None):
        res = self.read_cond(lambda x: re.search(r, x.buf), timeout)
        s = re.search(r, res).group(0)
        pos = res.find(s) + len(s)
        self.buf = res[pos:]
        return res[:pos]

    def read_nbytes(self, n, timeout=None):
        res = self.read_cond(lambda x: len(x.buf) >= n, timeout)
        self.buf = res[n:]
        return res[:n]

    def read_cond(self, cond, timeout=None):
        time_start = time()
        remaining = timeout
        if timeout is None:
            timeout = self.timeout

        if self.eof and not self.buf:
            raise EOFError("Connection closed")

        while not cond(self):
            self.fill_one(remaining)
            if cond(self):
                return self.buf

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
        return self.buf

    def fill_one(self, timeout=None):
        """Read something from socket.
        timeout = -1  -  blocking until read
        timeout = 0   -  non-blocking
        timeout = N   -  blocking until read or timeout
        """
        if timeout == None:
            timeout = self.timeout

        if timeout == 0:
            self.sock.setblocking(False)
            try:
                self.buf += self.sock.recv(4096)
            except SocketError:
                pass
            return
        
        if timeout == -1:
            self.sock.settimeout(None)  # blocking, infinity timeout
        else:
            self.sock.setblocking(True)  # it's overriden by settimeout, but for clarity
            self.sock.settimeout(timeout)
        
        buf = self.sock.recv(4096)
        self.eof = (not buf)
        self.buf += buf
        return

    def set_socket(self, sock):
        self.sock = sock
        return

    def get_socket(self):
        return self.sock

    def get_fileno(self):
        return self.sock.fileno()

    def write(self, s):
        return self.sock.sendall(s)

    def send(self, s):
        return self.sock.sendall(s)

    def shut_wr(self):
        self.sock.shutdown(socket.SHUT_WR)

    def shut_rd(self):
        self.sock.shutdown(socket.SHUT_RD)

    def close(self):
        return self.sock.close()

    def __del__(self):
        self.sock.close()

class Sock6(Sock):
    SOCKET_FAMILY = socket.AF_INET6

# Class to convert a socket into Sock class
# client sockets (returned by 'accept') can be coverted too
class toSock(Sock):
    def __init__(self, sock, timeout=None):
        self.timeout = timeout
        self.buf = ""
        self.eof = False

        self.sock = sock
        if timeout is None:
            self.timeout = DEFAULT_TIMEOUT
        self.sock.settimeout(timeout)
        return