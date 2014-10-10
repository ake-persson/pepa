#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Setup script for pepa
'''

from setuptools import setup

#VERSION = __import__('pepa').__version__
CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: POSIX :: Linux',
]

setup(
    name             = 'pepa',
    version          = '0.6.6',
#    version         = VERSION,

    description      = 'Configuration templating for SaltStack using Hierarchical substitution and Jinja',
    long_description = open("README.rst").read(),

    author           = 'Michael Persson',
    author_email     = 'michael.ake.persson@gmail.com',
    url              = 'https://github.com/mickep76/pepa.git',
    license          = 'Apache License 2.0',

    packages         = ['pepa'],

    classifiers      = CLASSIFIERS,
)
