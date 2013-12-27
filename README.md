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
f = Sock6("::1 3123", 3)
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

About
---------------------

This software uses Semantic Versioning ( http://semver.org/ )

Author: hellman ( hellman1908@gmail.com )

License: MIT License (http://opensource.org/licenses/MIT)
