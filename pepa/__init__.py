# -*- coding: utf-8 -*-
'''
Configuration templating for SaltStack using Hierarchical substitution and Jinja
'''

__author__ = 'Michael Persson <michael.ake.persson@gmail.com>'
__copyright__ = 'Copyright (c) 2013 Michael Persson'
__license__ = 'Apache License, Version 2.0'
__version__ = '0.6.6'

# Import python libs
import sys
import glob
import yaml
import jinja2
import re
from os.path import isfile, join
import logging
import __main__

logger = logging.getLogger(__name__)

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
        output['hostname'] = minion_id

        for categ, cdata in [s.items()[0] for s in self.sequence]:
            if categ not in output:
                logger.warn("Category is not defined: {0}".format(categ))
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
                logger.warn("Category has no value set: {0}".format(categ))
                continue
            else:
                entries = [output[categ]]

            res = None
            for entry in entries:
                fn = join(tdir, re.sub(r'\W', '_', entry.lower()) + '.yaml')
                if not isfile(fn):
                    logger.info("Template doesn't exist: {0}".format(fn))
                    continue

                logger.info("Loading template: {0}".format(fn))
                template = jinja2.Template(open(fn).read())

                inp = key_value_to_tree(output, self.delimiter)
                inp['grains'] = grains.copy()
                inp['pillar'] = pillar.copy()
                try:
                    res_jinja = template.render(inp)
                except Exception, e:
                    logger.error('Failed to parse JINJA in template: {0}\n{1}'.format(fn, e))

                try:
                    res_yaml = yaml.load(res_jinja)
                except Exception, e:
                    logger.error('Failed to parse YAML in template: {0}\n{1}'.format(fn, e))

                if res_yaml:
                    for key in res_yaml:
                        logger.debug("Substitute key {0}: {1}".format(key, res_yaml[key]))
                        output[key] = res_yaml[key]

        return key_value_to_tree(output, self.delimiter)
