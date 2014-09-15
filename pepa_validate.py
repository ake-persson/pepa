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

log = None

parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='Hostname')
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

#def _jinja2_filter_pepa_def(var, default=''):
#    try:
#        var
#    except NameError:
#        return default
#    return var

#def _jinja_define_pepadef(var, default=''):
#    return ''

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


defaults = key_value_to_tree(yaml.load(open(basedir + '/' + resource + '/validate/default.yaml').read()))

for fn in glob.glob(basedir + '/' + resource + '/*/*.yaml'):
    print('\n\n### Load template {0} ###\n\n'.format(fn))

#    env = jinja2.Environment(loader=jinja2.FileSystemLoader(dirname(fn)))
#    env.filters['pepa_def'] = _jinja2_filter_pepa_def
#    env.globals.update(pepadef=_jinja_define_pepadef)
#    tmpl = env.get_template(basename(fn))
#    tmpl.render()

    template = jinja2.Template(open(fn).read())
    result = None
    try:
        result = template.render(defaults)
        print result
    except jinja2.UndefinedError, e:
        print e

    try:
        yaml.load(result)
    except yaml.YAMLError, e:
       print e
