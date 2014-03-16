#!/usr/bin/env python
#-*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="sock",
    version="0.3.0",
    description="Small scripts to simplify network communication",
    long_description=open('README.md').read(),
    license="MIT",
    author="Alexey Hellman",
    author_email="hellman1908@gmail.com",
    url="https://github.com/hellman/sock",
    packages=find_packages(),
    py_modules=['sock'],
    test_suite="test_sock.TestParseAddr",
)
