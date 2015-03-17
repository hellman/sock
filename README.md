sock
====================

Small script to simplify network communication.
Something like telnetlib http://docs.python.org/library/telnetlib.html, but for clean TCP/UDP (no command sequences, \r\n newlines, etc.)


Usage
---------------------

###TCP Client

```python
from sock import *

f = Sock("some.cool.servi.ce:3123", timeout=10)
# or IPv6
f = Sock6("::1 3123", timeout=3)
# or already existing socket
f = Sock.from_socket(some_socket)  # or toSock(some_socket)
# or UDP/IPv6
f = SockU6("::1 3123", timeout=3)

# wait for prompt (skip banner for example)
# the prompt itself will be skipped (and returned) too
f.read_until("> ", timeout=3)  # read_until_re also exists

f.send("flip coin\n")

# skip until regexp
result1 = f.skip_until_re(r"You've got (heads|tails)")  # skip_until(str) also exists

# read until also consumes matched part
f.read_until_re(r"You've g[oe]t ")  # read_until(str) also exists

# read specific number of bytes
result2 = f.read_nbytes(5)

assert result1 == result2

# alias for f.send(s + "\n")
f.send_line("random please")

# read one packet and flush buffers
print f.read_one()

# non-blocking read (flush buffers)
print f.read_one(0)

# read until disconnect
print f.read_all()
```

About
---------------------

This software uses Semantic Versioning ( http://semver.org/ )

Author: hellman ( hellman1908@gmail.com )

License: MIT License (http://opensource.org/licenses/MIT)
