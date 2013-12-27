# -*- coding: utf-8 -*-

import unittest

from itertools import product

from sock import parse_addr


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


if __name__ == "__main__":
    unittest.main()
