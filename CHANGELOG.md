## 0.4.0 (unreleased)

  - sock.interact() - wrapper for telnetlib interact
  - Sock.from_socket() - alias for toSock
  - read/skip _until_re return string instead of match if number of groups <= 1 (similar to re.findall)


## 0.3.0 (30.12.2013)

  - read/skip \_until\_re now return regexp match (usefull for quick parsing)
  - added send\_line alias


## 0.2.0 (27.12.2013)

  - restored first address format: Sock("ip", port)
  - added small udp support
  - removed server classes
