#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Setup script for pepa
'''

from setuptools import setup, find_packages
import sys, os

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: POSIX :: Linux',
]

setup(
    name             = 'pepa',
    version          = __version__,

    description      = 'Configuration templating for SaltStack using Hierarchical substitution and Jinja',
    long_description = open("README.rst").read(),

    author           = 'Michael Persson',
    author_email     = 'michael.ake.persson@gmail.com',
    url              = 'https://github.com/mickep76/pepa.git',
    license          = 'Apache License, Version 2.0',

    packages         = find_packages(exclude=['examples', 'tests']),
    classifiers      = CLASSIFIERS,
    scripts          = ['scripts/pepa', 'scripts/pepa-test'],
    install_requires = open("requirements.txt").readlines(),
)
