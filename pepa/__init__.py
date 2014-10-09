# -*- coding: utf-8 -*-
'''
Configuration templating for SaltStack using Hierarchical substitution and Jinja
'''

__author__ = 'Michael Persson <michael.ake.persson@gmail.com>'
__copyright__ = 'Copyright (c) 2013 Michael Persson'
__license__ = 'Apache License, Version 2.0'
__version__ = '0.6.6'

# Import python libs
import logging
import sys
import glob
import yaml
import jinja2
import re
from os.path import isfile, join

# Set up logging
log = logging.getLogger(__name__)

def key_value_to_tree(data, delimiter):
    '''
    Convert key/value to tree
    '''
    tree = {}
    for flatkey, value in data.items():
        t = tree
        keys = flatkey.split(delimiter)
        for key in keys:
            if key == keys[-1]:
                t[key] = value
            else:
                t = t.setdefault(key, {})
    return tree

class Template():
    '''
    Template class
    '''
    def __init__(self, roots = { 'base': '/srv/pepa' }, delimiter = '..', resource = 'host', sequence = { 'hostname': { 'name': 'input', 'base_only': True } }):
        '''
        Initialize template object
        '''
        self.roots = roots
        self.delimiter = delimiter
        self.resource = resource
        self.sequence = sequence

    def compile(self, minion_id, grains = {}, pillar = {}, environment = 'base'):
        '''
        Compile templates
        '''

        # Default
        output = {}
        output['default'] = 'default'

        

        for categ, cdata in [s.items()[0] for s in self.sequence]:
            if categ not in output:
                log.warn("Category is not defined: {0}".format(categ))
                continue

            # Category alias
            calias = categ
            if isinstance(cdata, dict) and 'name' in cdata:
                calias = cdata['name']

            # Template dir.
            tdir = join(self.roots[environment], self.resource, calias)
            if cdata and 'base_only' in cdata and cdata['base_only']:
                tdir = join(self.roots['base'], self.resource, calias)

            entries = []
            if isinstance(output[categ], list):
                entries = output[categ]
            elif not output[categ]:
                log.warn("Category has no value set: {0}".format(categ))
                continue
            else:
                entries = [output[categ]]

            res = None
            for entry in entries:
                fn = join(tdir, re.sub(r'\W', '_', entry.lower()) + '.yaml')
                if not isfile(fn):
                    log.info("Template doesn't exist: {0}".format(fn))
                    continue

                log.info("Loading template: {0}".format(fn))
                template = jinja2.Template(open(fn).read())

                inp = key_value_to_tree(output, delimiter)
                inp['grains'] = grains.copy()
                inp['pillar'] = pillar.copy()
                try:
                    res_jinja = template.render(inp)
                except Exception, e:
                    log.error('Failed to parse JINJA in template: {0}\n{1}'.format(fn, e))

                try:
                    res_yaml = yaml.load(res_jinja)
                except Exception, e:
                    log.error('Failed to parse YAML in template: {0}\n{1}'.format(fn, e))

#                if res:
#                    for key in res:
