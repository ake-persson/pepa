#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Validate Pepa templates
'''

__author__ = 'Michael Persson <michael.ake.persson@gmail.com>'
__copyright__ = 'Copyright (c) 2013 Michael Persson'
__license__ = 'Apache License, Version 2.0'
__version__ = '0.0.2'

# Import python libs
import logging
import sys
import glob
import yaml
import jinja2
import re
from os.path import isfile, isdir, join, dirname, basename
import argparse
import cerberus
import pygments
import pygments.lexers
import pygments.formatters

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

def validate_templates():
    '''
    Parse Pepa templates
    '''
    success = True
    resdir = join(roots['base'], resource)
    schema = {}
    if isfile(resdir + '/schema.yaml'):
        log.debug('Load schema {0}'.format(resdir + '/schema.yaml'))
        schema = yaml.load(open(resdir + '/schema.yaml').read())

    for categ, info in [s.items()[0] for s in sequence]:
        templdir = join(roots['base'], resource, categ)
        if isinstance(info, dict) and 'name' in info:
            templdir = join(roots['base'], resource, info['name'])

        if not isdir(templdir + '/tests'):
            continue

        for testf in glob.glob(templdir + '/tests/*.yaml'):
            log.debug('Load input {0}'.format(testf))

            defaults = key_value_to_tree(yaml.load(open(testf).read()))

            for fn in glob.glob(templdir + '/*.yaml'):
                log.debug('Load template {0}'.format(fn))

                template = jinja2.Template(open(fn).read())
                res_jinja = None
                res_yaml = None
                try:
                    res_jinja = template.render(defaults)
                except Exception, e:
                    success = False
                    log.error('Failed to parse JINJA template {0}\n{1}'.format(fn, e))
                    continue
                try:
                    res_yaml = yaml.load(res_jinja)
                except Exception, e:
                    success = False
                    log.error('Failed to parse YAML in template {0}\n{1}'.format(fn, e))

                if args.show:
                    print pygments.highlight(yaml.safe_dump(res_yaml), pygments.lexers.YamlLexer(), pygments.formatters.TerminalFormatter())

                val = cerberus.Validator()
                try:
                    status = val.validate(res_yaml, schema)
                    if not status:
                        for ekey, error in val.errors.items():
                            log.warning('Validation failed for key {0}: {1}'.format(ekey, error))
                except Exception, e:
                    log.warn('Failed to validate output for template {0}\n{1}'.format(fn, e))

    return success

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', default='/etc/salt/master', help='Configuration file')
parser.add_argument('-d', '--debug', action='store_true', help='Print debug info')
parser.add_argument('-s', '--show', action='store_true', help='Show result of template')
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

if not validate_templates():
    sys.exit(1)
