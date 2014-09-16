#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Validate Pepa templates
'''

__author__ = 'Michael Persson <michael.ake.persson@gmail.com>'
__copyright__ = 'Copyright (c) 2013 Michael Persson'
__license__ = 'Apache License, Version 2.0'
__version__ = '0.0.1'

# Import python libs
import logging
import sys
import glob
import yaml
import jinja2
import re
from os.path import isfile, join, dirname, basename
import argparse

# Options
__opts__ = {
    'pepa_roots': {
        'base': '/srv/salt'
    },
    'pepa_delimiter': '..'
}

log = None

def key_value_to_tree(data):
    '''
    Convert key/value to tree
    '''
    tree = {}
    for flatkey, value in data.items():
        t = tree
        keys = flatkey.split('..')
        for key in keys:
            if key == keys[-1]:
                t[key] = value
            else:
                t = t.setdefault(key, {})
    return tree

def validate_template(deffn, defaults):
    '''
    Parse Pepa templates
    '''
    success = True
    if args.teamcity:
        print "##teamcity[testSuiteStarted name='Validate Pepa Templates using defaults {0}' captureStandardOutput='true']".format(deffn)
    for categ, info in [s.items()[0] for s in sequence]:
        templdir = join(roots['base'], resource, categ)
        if isinstance(info, dict) and 'name' in info:
            templdir = join(roots['base'], resource, info['name'])

        for fn in glob.glob(templdir + '/*.yaml'):
            if args.teamcity:
                print "##teamcity[testStarted name='Parse JINJA file {0}' captureStandardOutput='true']".format(fn)
            else:
                log.debug('Load template {0}'.format(fn))

            template = jinja2.Template(open(fn).read())
            result = None
            try:
                result = template.render(defaults)
            except jinja2.UndefinedError, e:
                success = False
                if args.teamcity:
                    print "##teamcity[testFailed name='Parse JINJA template {0}' message='Failed to parse JINJA template']\n{1}".format(fn, e)
                else:
                    log.error('Failed to parse JINJA template {0}\n{1}'.format(fn, e))

            if args.teamcity:
                print "##teamcity[testFinished name='Parse JINJA template {0}']".format(fn)
                print "##teamcity[testStarted name='Parse YAML in template {0}' captureStandardOutput='true']".format(fn)
            try:
                yaml.load(result)
            except yaml.YAMLError, e:
                success = False
                if args.teamcity:
                    print "##teamcity[testFailed name='Parse YAML in template {0}' message='Failed to parse YAML in template']\n{1}".format(fn, e)
                else:
                    log.error('Failed to parse YAML in template {0}\n{1}'.format(fn, e))

    if args.teamcity:
        print "##teamcity[testSuiteFinished name='Validate Pepa Templates using defaults {0}']".format(deffn)

    return success

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', default='/etc/salt/master', help='Configuration file')
parser.add_argument('-d', '--debug', action='store_true', help='Print debug info')
parser.add_argument('-n', '--no-color', action='store_true', help='No color output')
parser.add_argument('-t', '--teamcity', action='store_true', help='Output validation in TeamCity format')
args = parser.parse_args()

LOG_LEVEL = logging.WARNING
if args.debug:
    LOG_LEVEL = logging.DEBUG

formatter = None
if not args.no_color:
    try:
        import colorlog
        formatter = colorlog.ColoredFormatter("[%(log_color)s%(levelname)-8s%(reset)s] %(log_color)s%(message)s%(reset)s")
    except ImportError:
        formatter = logging.Formatter("[%(levelname)-8s] %(message)s")
else:
    formatter = logging.Formatter("[%(levelname)-8s] %(message)s")

stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)

log = logging.getLogger('pythonConfig')
log.setLevel(LOG_LEVEL)
log.addHandler(stream)

# Load configuration file
if not isfile(args.config):
    log.critical('Configuration file doesn\'t exist {0}'.format(args.config))
    sys.exit(1)

# Get configuration
__opts__.update(yaml.load(open(args.config).read()))

loc = 0
for name in [e.keys()[0] for e in __opts__['ext_pillar']]:
    if name == 'pepa':
        break
    loc += 1

roots = __opts__['pepa_roots']
resource = __opts__['ext_pillar'][loc]['pepa']['resource']
sequence = __opts__['ext_pillar'][loc]['pepa']['sequence']

# Load default test values
defdir = join(roots['base'], resource, 'test/defaults')
for fn in glob.glob(defdir + '/*.yaml'):
    try:
        validate_template(fn, key_value_to_tree(yaml.load(open(fn).read())))
    except yaml.YAMLError, e:
        log.critical('Failed to parse YAML file {0}\n{1}'.format(fn, e))
        sys.exit(1)
