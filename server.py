#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys
import time
import threading
from socket import *

__all__ = "tcp tcp6 udp udp6".split()

# IPv4/IPv6 --------------------

class inet:
    SOCKET_FAMILY = AF_INET
    DEFAULT_HOST = "0.0.0.0"

    def __init__(self, port, handler, host=None):
        self.port = int(port)
        self.handler = handler
        self.host = host if host else self.DEFAULT_HOST
        self.socket = socket(self.SOCKET_FAMILY, self.SOCKET_TYPE)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))

class inet6(inet):
    SOCKET_FAMILY = AF_INET6
    DEFAULT_HOST = "::"


# UDP --------------------------
# udp handler accepts (client, data, addr) arguments

class udp(inet):
    SOCKET_TYPE = SOCK_DGRAM
    def listen(self, maxthreads=10, debug=True):
        if debug: print "[i] %s Started UDP server on [%s]:%d" % (time.asctime(), self.host, self.port)
        while True:
            data, addr = self.socket.recvfrom(4096)
            if debug: print "[i]", time.asctime(), "Connect from %s" % (addr, )
            
            while threading.active_count() - 1 >= maxthreads:
                if debug: sys.stderr.write("[W] WARNING: Too many threads! %d\n" % threading.active_count())
                time.sleep(1)

            t = threading.Thread(target=self.handler, args=(self.socket, data, addr))
            t.setDaemon(True)
            t.start()
        return

class udp6(inet6, udp):
    pass


# TCP --------------------------
# tcp handler accepts (client, addr) arguments

class tcp(inet):
    SOCKET_TYPE = SOCK_STREAM
    def listen(self, maxthreads=1000, maxconn=100, debug=True):
        self.socket.listen(maxconn)
        if debug: print "[i] %s Started TCP server on [%s]%d" % (time.asctime(), self.host, self.port)
        while True:
            client, addr = self.socket.accept()
            if debug: print "[i]", time.asctime(), "Connect from", addr
            
            while threading.active_count() - 1 >= maxthreads:
                if debug: sys.stderr.write("[W] WARNING: Too many threads! %d\n" % threading.active_count())
                time.sleep(0.5)

            t = threading.Thread(target=self.handler, args=(client, addr))
            t.setDaemon(True)
            t.start()
        return

class tcp6(inet6, tcp):
    pass