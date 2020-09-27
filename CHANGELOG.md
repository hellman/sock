## 0.5.0 (Sep 27, 2020)

  - swtich to python 3
  - ssl wrapper

## 0.4.0 (Mar 17, 2015)

  - sock.interact() - wrapper for telnetlib interact
  - Sock.from_socket() - alias for toSock
  - read/skip \_until\_re return string instead of match if number of groups <= 1 (similar to re.findall)

## 0.3.0 (Dec 30, 2013)

  - read/skip \_until\_re now return regexp match (usefull for quick parsing)
  - added send\_line alias

## 0.2.0 (Dec 27, 2013)

  - restored first address format: Sock("ip", port)
  - added small udp support
  - removed server classes
