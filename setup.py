#!/usr/bin/env python3

from distutils.core import setup

REQUIRES = [line.strip() for line in open('requirements.txt') if line.strip()]

setup(
    name='ezsnmp',
    version='0.1',
    packages=['ezsnmp', 'ezsnmp.devices'],
    install_requires=REQUIRES,
    url='https://github.com/Sedl/pyezsnmp'
)
