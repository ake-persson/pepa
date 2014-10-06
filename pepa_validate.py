#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
'''
Validate Pepa templates
'''

__author__ = 'Michael Persson <michael.ake.persson@gmail.com>'
__copyright__ = 'Copyright (c) 2013 Michael Persson'
__license__ = 'Apache License, Version 2.0'
__version__ = '0.0.4'

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
    Validate Pepa templates
    '''
    success = True
    resdir = join(roots['base'], resource)
    schema = {}
    for fn in glob.glob(resdir + '/schemas/*.yaml'):
        sfn = 'schemas/' + basename(fn)
        log.debug('Load schema {0}'.format(sfn))

        template = jinja2.Template(open(fn).read())
        try:
            res_jinja = template.render()
        except Exception, e:
            log.critical('Failed to parse YAML in schema {0}\n{1}'.format(sfn, e))
            sys.exit(1)
        try:
            res_yaml = yaml.load(res_jinja)
        except Exception, e:
            log.critical('Failed to parse YAML in test {0}\n{1}'.format(stestf, e))
            sys.exit(1)
        schema.update(res_yaml)

        if args.show:
            print '### Schema: {0} ###\n'.format(resdir + '/schema.yaml')
            print yaml.safe_dump(res_yaml, default_flow_style=False)

    for categ, info in [s.items()[0] for s in sequence]:
        templdir = join(roots['base'], resource, categ)
        alias = categ
        if isinstance(info, dict) and 'name' in info:
            alias = info['name']
            templdir = join(roots['base'], resource, alias)

        if not isdir(templdir + '/tests'):
            success = False
            log.error('No tests defined for category {0}'.format(alias))
            continue

        for testf in glob.glob(templdir + '/tests/*.yaml'):
            stestf = alias + '/tests/' + basename(testf)
            log.debug('Load test {0}'.format(stestf))

            # Load tests
            template = jinja2.Template(open(testf).read())
            try:
                res_jinja = template.render()
            except Exception, e:
                log.critical('Failed to parse Jinja test {0}\n{1}'.format(stestf, e))
                sys.exit(1)
            try:
                res_yaml = yaml.load(res_jinja)
            except:
                log.critical('Failed to parse YAML in test {0}\n{1}'.format(stestf, e))
                sys.exit(1)

            if args.show:
                print '### Test: {0} ###\n'.format(stestf)
                print yaml.safe_dump(res_yaml, default_flow_style=False)

            defaults = key_value_to_tree(res_yaml)

            for fn in glob.glob(templdir + '/*.yaml'):
                sfn = alias + '/' + basename(fn)

                log.debug('Load template {0}'.format(sfn))

                # Parse Jinja
                template = jinja2.Template(open(fn).read())
                res_jinja = None
                res_yaml = None
                try:
                    res_jinja = template.render(defaults)
                except Exception, e:
                    success = False
                    log.critical('Failed to parse Jinja template {0}\n{1}'.format(sfn, e))
                    continue

                # Parse YAML
                try:
                    res_yaml = yaml.load(res_jinja)
                except Exception, e:
                    success = False
                    log.critical('Failed to parse YAML in template {0}\n{1}'.format(sfn, e))

                # Validate operators
                if not res_yaml:
                    continue

                for key in res_yaml:
                    skey = key.rsplit(__opts__['pepa_delimiter'], 1)
                    rkey = None
                    operator = None
                    if len(skey) > 1 and key.rfind('()') > 0:
                        rkey = skey[0].rstrip(__opts__['pepa_delimiter'])
                        operator = skey[1]

                    if operator == 'merge()' or operator == 'imerge()' or operator == 'immutable()':
                        res_yaml[rkey] = res_yaml[key]
                        del res_yaml[key]
                    elif operator == 'unset' or operator == 'iunset':
                        del res_yaml[key]
                    elif operator is not None:
                        success = False
                        log.error('Unsupported operator {0} in template {1}'.format(operator, rkey, sfn))

                if args.show:
                    print '### Template: {0} ###\n'.format(fn)
                    print yaml.safe_dump(res_yaml, default_flow_style=False)

                val = cerberus.Validator()
                try:
                    status = val.validate(res_yaml, schema)
                    if not status:
                        success = False
                        for ekey, error in val.errors.items():
                            log.error('Incorrect key {0} in template {1}: {2}'.format(ekey, sfn, error))
                except Exception, e:
                    success = False
                    log.error('Failed to validate output for template {0}: {1}'.format(sfn, e))

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
if args.teamcity:
    formatter = logging.Formatter("##teamcity[message text='%(message)s' status='%(levelname)s']")
elif not args.no_color:
    try:
        import colorlog
        formatter = colorlog.ColoredFormatter("[%(log_color)s%(levelname)-8s%(reset)s] %(log_color)s%(message)s%(reset)s")
    except ImportError:
        formatter = logging.Formatter("[%(levelname)-8s] %(message)s")
else:
    formatter = logging.Formatter("[%(levelname)-8s] %(message)s")

yaml.dumper.SafeDumper.ignore_aliases = lambda self, data: True

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
