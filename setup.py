#!/usr/bin/env python
#-*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="sock",
    version="0.4.0",

    author="hellman",
    author_email="hellman1908@gmail.com",
    license="MIT",

    description="Small script to simplify network communication",
    long_description=open('README.md').read(),
    keywords="socket telnet network sock",

    url="https://github.com/hellman/sock",
    packages=find_packages(),
    py_modules=['sock'],

    test_suite="test_sock.TestParseAddr",

    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Developers',
                 'Natural Language :: English',
                 'Operating System :: Unix',
                 'Programming Language :: Python :: 2',
                 'License :: OSI Approved :: MIT License',
                 'Topic :: System :: Networking',
                 ],
)
