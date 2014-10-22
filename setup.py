#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Setup script for pepa
'''

from setuptools import setup, find_packages
import sys, os
from pillar.pepa import __author__, __author_email__, __url__, __version__, __license__

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: ' + __license__,
    'Operating System :: POSIX :: Linux',
]
SCRIPTS = [
    'scripts/pepa',
    'scripts/pepa-test',
]

setup(
    name             = 'pepa',
    version          = __version__,

    description      = 'Configuration templating for SaltStack using Hierarchical substitution and Jinja',
    long_description = open("README.rst").read(),

    author           = __author__,
    author_email     = __author_email__,
    url              = __url__,
    license          = __license__,

    packages         = find_packages(exclude=['examples', 'tests']),
    classifiers      = CLASSIFIERS,
    scripts          = SCRIPTS,
    install_requires = open("requirements.txt").readlines(),
)
