# -*- coding: utf-8 -*-

import unittest

from itertools import product

from sock import parse_addr, Sock, Sock6, SockU, SockU6


class TestParseAddr(unittest.TestCase):
    HOSTS = (
        """
        127.0.0.1  8.8.8.8  255.255.255.255  1.1.1.1
        fe80::0  FE80:0000:0000:0000:0202:B3FF:FE1E:8329  FE80::0202:B3FF:FE1E:8329  [2001:db8:0:1]
        example.com  x.x  localhost  some.bigdomain  somehost x.y.z.w.a_1._b.z
        """
    ).strip().split()

    PORTS = (
        0, 1, 2, 3, 21, 80, 443, 1024, 1337, 3123, 31337, 5000, 65534, 65535
    )

    def test_good(self):
        for host, port in product(self.HOSTS, self.PORTS):
            good = (host.strip("[]"), port)

            self.assertEqual( parse_addr(host, port), good)
            self.assertEqual( parse_addr((host, port)), good)
            self.assertEqual( parse_addr("%s:%s" % (host, port)), good)
            self.assertEqual( parse_addr("%s: %s" % (host, port)), good)
            self.assertEqual( parse_addr("%s|%s" % (host, port)), good)
            self.assertEqual( parse_addr("%s/%s" % (host, port)), good)
            self.assertEqual( parse_addr("%s %s" % (host, port)), good)
            self.assertEqual( parse_addr("%s:| /%s" % (host, port)), good)
            self.assertEqual( parse_addr("%s;%s" % (host, port)), good)

    def test_bad(self):
        for host, port in product(self.HOSTS, self.PORTS):
            self.assertRaises(TypeError, parse_addr, (host, port), port)
            self.assertRaises(TypeError, parse_addr, (host,), port)


class TestConnects(unittest.TestCase):
    HTTP_HOSTS = "google.com".strip().split()
    DNS_HOSTS = "8.8.8.8".strip().split()

    def test_http(self):
        for host in self.HTTP_HOSTS:
            f = Sock(host, 80)
            f.send("GET / HTTP/1.1\r\n\r\n")
            line = f.read_line()
            self.assertTrue(line.startswith("HTTP/1.1 "))
            f.close()

    def test_dns(self):
        query = "241a010000010000000000000377777706676f6f676c6503636f6d0000010001".decode("hex")
        marker = "\x03www\x06google\x03com"
        for host in self.DNS_HOSTS:
            f = SockU(host, 53)
            f.send(query)
            line = f.read_one()
            self.assertIn(marker, line)
            f.close()


if __name__ == "__main__":
    unittest.main()
