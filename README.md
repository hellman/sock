sock
====================

Small scripts to simplify network communication.

### TCP client:
Something like telnetlib http://docs.python.org/library/telnetlib.html, but for clean TCP (no command sequences, \r\n newlines, etc.)

### TCP/UDP binders
Simple threaded tcp/udp servers - kind of simplified SocketServer http://docs.python.org/library/socketserver.html.

Usage
---------------------

###TCP Client 

```python
from sock import *

f = Sock("some.cool.servi.ce", 3123, timeout=10)
# or IPv6
f = Sock6("::1", 3123, 3)
# or already existing socket
f = toSock(some_socket)

# wait for prompt (skip banner for example)
# the prompt itself will be skipped too
f.read_until("> ", timeout=3)  # read_until_re also exists

f.send("flip coin\n")

# wait for regexp
# 'wait' means that the match won't be skipped
f.wait_for_re(r"You've got (heads|tails)")    # wait_for also exists

# read specific number of bytes
result = f.read_nbytes(11+5)[11:16]

f.send("random please\n")

# read one packet and flush buffers
print f.read_one()

# non-blocking read (flush buffers)
print f.read_one(0)

# read until disconnect
print f.read_all()
```

###TCP binder

```python
from server import *

def handler(client, addr):
	client.send("Hello, I'm server!\n")
	client.send(client.recv(4096))

tcp(3123, handler).listen()
# or IPv6
tcp6(3123, handler).listen()
```

###UDP binder

```python
from server import *

def handler(sock, data, addr):
	sock.sendto("Hello, I'm server!\n" + data, addr)

udp(3123, handler).listen()
# or IPv6
udp6(3123, handler).listen()
```

About
---------------------

Author: hellman ( hellman1908@gmail.com )

License: GNU General Public License v2 (http://opensource.org/licenses/gpl-2.0.php)
