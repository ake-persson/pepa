#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Validate shit!
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

basedir = 'examples'
resource = 'hosts'

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

# Load defaults file
fn = join(basedir, resource, 'validate', 'default.yaml')
log.debug('Load defaults file {0}'.format(fn))
if not isfile(fn):
    log.critical('Defaults file doesn\'t exist {0}'.format(fn))
    sys.exit(1)

defaults = None
try:
    defaults = key_value_to_tree(yaml.load(open(fn).read()))
except yaml.YAMLError, e:
    log.critical('Failed to parse YAML file {0}\n{1}'.format(fn, e))
    sys.exit(1)

# Parse Pepa templates
roots = __opts__['pepa_roots']
resource = __opts__['ext_pillar'][loc]['pepa']['resource']
sequence = __opts__['ext_pillar'][loc]['pepa']['sequence']

for categ, info in [s.items()[0] for s in sequence]:
    templdir = join(roots['base'], resource, categ)
    if isinstance(info, dict) and 'name' in info:
        templdir = join(roots['base'], resource, info['name'])

    for fn in glob.glob(templdir + '/*.yaml'):
        log.debug('Load template {0}'.format(fn))

        template = jinja2.Template(open(fn).read())
        result = None
        try:
            result = template.render(defaults)
        except jinja2.UndefinedError, e:
            log.error('Failed to parse JINJA template {0}\n{1}'.format(fn, e))

        try:
            yaml.load(result)
        except yaml.YAMLError, e:
            log.error('Failed to parse YAML file {0}\n{1}'.format(fn, e))
