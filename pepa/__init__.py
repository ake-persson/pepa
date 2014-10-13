# -*- coding: utf-8 -*-
'''
Configuration templating for SaltStack using Hierarchical substitution and Jinja
'''

__author__ = 'Michael Persson <michael.ake.persson@gmail.com>'
__copyright__ = 'Copyright (c) 2013 Michael Persson'
__license__ = 'Apache License, Version 2.0'
__version__ = '0.7.5'

# Import python libs
import sys
import glob
import yaml
import jinja2
import re
from os.path import isfile, isdir, join, dirname, basename
import logging
import cerberus

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

class Template(object):
    '''
    Template class
    '''
    def __init__(self, roots={'base': '/srv/pepa'}, delimiter='..', resource='host', sequence={'hostname': {'name': 'input', 'base_only': True}}, subkey=False, subkey_only=False):
        '''
        Initialize template object
        '''
        self.roots = roots
        self.delimiter = delimiter
        self.resource = resource
        self.sequence = sequence
        self.subkey = subkey
        self.subkey_only = subkey_only

    def compile(self, minion_id, grains={}, pillar={}):
        '''
        Compile templates
        '''

        # Default
        output = {}
        output['default'] = 'default'
        output['hostname'] = minion_id

        # Environment
        if 'environment' in pillar:
            output['environment'] = pillar['environment']
        elif 'environment' in grains:
            output['environment'] = grains['environment']
        else:
            output['environment'] = 'base'

        immutable = {}

        for categ, cdata in [s.items()[0] for s in self.sequence]:
            if categ not in output:
                logger.warn("Category is not defined: {0}".format(categ))
                continue

            # Category alias
            calias = categ
            if isinstance(cdata, dict) and 'name' in cdata:
                calias = cdata['name']

            # Template dir.
            tdir = join(self.roots[output['environment']], self.resource, calias)
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
                    return {}

                try:
                    results = yaml.load(res_jinja)
                except Exception, e:
                    logger.error('Failed to parse YAML in template: {0}\n{1}'.format(fn, e))
                    return {}

                if not results:
                    continue

                for key in results:
                    skey = key.rsplit(self.delimiter, 1)
                    rkey = None
                    operator = None
                    if len(skey) > 1 and key.rfind('()') > 0:
                        rkey = skey[0].rstrip(self.delimiter)
                        operator = skey[1]

                    if key in immutable:
                        logger.warning('Key {0} is immutable, changes are not allowed'.format(key))
                    elif rkey in immutable:
                        logger.warning("Key {0} is immutable, changes are not allowed".format(rkey))
                    elif operator == 'merge()' or operator == 'imerge()':
                        if operator == 'merge()':
                            logger.debug("Merge key {0}: {1}".format(rkey, results[key]))
                        else:
                            logger.debug("Set immutable and merge key {0}: {1}".format(rkey, results[key]))
                            immutable[rkey] = True
                        if rkey not in output:
                            logger.error('Cant\'t merge key {0} doesn\'t exist'.format(rkey))
                        elif type(results[key]) != type(output[rkey]):
                            logger.error('Can\'t merge different types for key {0}'.format(rkey))
                        elif type(results[key]) is dict:
                            output[rkey].update(results[key])
                        elif type(results[key]) is list:
                            output[rkey].extend(results[key])
                        else:
                            logger.error('Unsupported type need to be list or dict for key {0}'.format(rkey))
                    elif operator == 'unset()' or operator == 'iunset()':
                        if operator == 'unset()':
                            logger.debug("Unset key {0}".format(rkey))
                        else:
                            logger.debug("Set immutable and unset key {0}".format(rkey))
                            immutable[rkey] = True
                        if rkey in output:
                            del output[rkey]
                    elif operator == 'immutable()':
                        logger.debug("Set immutable and substitute key {0}: {1}".format(rkey, results[key]))
                        immutable[rkey] = True
                        output[rkey] = results[key]
                    elif operator is not None:
                        logger.error('Unsupported operator {0}, skipping key {1}'.format(operator, rkey))
                    else:
                        logger.debug("Substitute key {0}: {1}".format(key, results[key]))
                        output[key] = results[key]

        tree = key_value_to_tree(output, self.delimiter)
        pdata = {}
        if self.subkey_only:
            pdata[self.resource] = tree.copy()
        elif self.subkey:
            pdata = tree
            pdata[self.resource] = tree.copy()
        else:
            pdata = tree
        return pdata

    def test(self, show=False, teamcity=False):
        '''
        Test templates
        '''

        if teamcity:
            print "##teamcity[testSuiteStarted name='pepa']"

        success = True
        resdir = join(self.roots['base'], self.resource)
        schema = {}
        for fn in glob.glob(resdir + '/schemas/*.yaml'):
            sfn = 'schemas/' + basename(fn)
            logger.debug('Load schema {0}'.format(sfn))

            template = jinja2.Template(open(fn).read())
            try:
                res_jinja = template.render()
            except Exception, e:
                logger.critical('Failed to parse YAML in schema {0}\n{1}'.format(sfn, e))
                sys.exit(1)
            try:
                res_yaml = yaml.load(res_jinja)
            except Exception, e:
                logger.critical('Failed to parse YAML in test {0}\n{1}'.format(sfn, e))
                sys.exit(1)
            schema.update(res_yaml)

            if show:
                print '### Schema: {0} ###\n'.format(sfn)
                print yaml.safe_dump(res_yaml, default_flow_style=False)

        for categ, info in [s.items()[0] for s in self.sequence]:
            templdir = join(self.roots['base'], self.resource, categ)
            alias = categ
            if isinstance(info, dict) and 'name' in info:
                alias = info['name']
                templdir = join(self.roots['base'], self.resource, alias)

            if not isdir(templdir + '/tests'):
                success = False
                logger.error('No tests defined for category {0}'.format(alias))
                continue

            for testf in glob.glob(templdir + '/tests/*.yaml'):
                stestf = alias + '/tests/' + basename(testf)
                logger.debug('Load test {0}'.format(stestf))

                # Load tests
                template = jinja2.Template(open(testf).read())
                try:
                    res_jinja = template.render()
                except Exception, e:
                    logger.critical('Failed to parse Jinja test {0}\n{1}'.format(stestf, e))
                    sys.exit(1)
                try:
                    res_yaml = yaml.load(res_jinja)
                except Exception, e:
                    logger.critical('Failed to parse YAML in test {0}\n{1}'.format(stestf, e))
                    sys.exit(1)

                if show:
                    print '### Test: {0} ###\n'.format(stestf)
                    print yaml.safe_dump(res_yaml, default_flow_style=False)

                defaults = key_value_to_tree(res_yaml, self.delimiter)

                for fn in glob.glob(templdir + '/*.yaml'):
                    sfn = alias + '/' + basename(fn)

                    logger.debug('Load template {0}'.format(sfn))
                    if teamcity:
                        print "##teamcity[testStarted name='{0}']".format(sfn)

                    # Parse Jinja
                    template = jinja2.Template(open(fn).read())
                    res_jinja = None
                    res_yaml = None
                    try:
                        res_jinja = template.render(defaults)
                    except Exception, e:
                        success = False
                        if teamcity:
                            print "##teamcity[testFailed name='{0}' message='Failed to parse Jinja: {1}']".format(sfn, e)
                            print "##teamcity[testFinished name='{0}']".format(sfn)
                        else:
                            logger.critical('Failed to parse Jinja template {0}\n{1}'.format(sfn, e))
                        continue

                    # Parse YAML
                    try:
                        res_yaml = yaml.load(res_jinja)
                    except Exception, e:
                        success = False
                        if teamcity:
                            print "##teamcity[testFailed name='{0}' message='Failed to parse YAML: {1}']".format(sfn, e)
                            print "##teamcity[testFinished name='{0}']".format(sfn)
                        else:
                            logger.critical('Failed to parse YAML in template {0}\n{1}'.format(sfn, e))
                        continue

                    # Validate operators
                    if not res_yaml:
                        continue

                    for key in res_yaml:
                        skey = key.rsplit(self.delimiter, 1)
                        rkey = None
                        operator = None
                        if len(skey) > 1 and key.rfind('()') > 0:
                            rkey = skey[0].rstrip(self.delimiter)
                            operator = skey[1]

                        if operator == 'merge()' or operator == 'imerge()' or operator == 'immutable()':
                            res_yaml[rkey] = res_yaml[key]
                            del res_yaml[key]
                        elif operator == 'unset' or operator == 'iunset':
                            del res_yaml[key]
                        elif operator is not None:
                            success = False
                            if teamcity:
                                print "##teamcity[testFailed name='{0}' message='Unsupported operator {1}']".format(sfn, operator)
                            else:
                                logger.error('Unsupported operator {0} in template {1}'.format(operator, sfn))

                    if show:
                        print '### Template: {0} ###\n'.format(sfn)
                        print yaml.safe_dump(res_yaml, default_flow_style=False)

                    val = cerberus.Validator()
                    try:
                        status = val.validate(res_yaml, schema)
                        if not status:
                            success = False
                            for ekey, error in val.errors.items():
                                if teamcity:
                                    print "##teamcity[testFailed name='{0}' message='{1}: {2}']".format(sfn, ekey, error)
                                else:
                                    logger.error('Incorrect key {0} in template {1}: {2}'.format(ekey, sfn, error))
                    except Exception, e:
                        success = False
                        if teamcity:
                            print "##teamcity[testFailed name='{0}' message='Failed to validate output for template: {1}']".format(sfn, e)
                        else:
                            logger.error('Failed to validate output for template {0}: {1}'.format(sfn, e))

                    if teamcity:
                        print "##teamcity[testFinished name='{0}']".format(sfn)

        if teamcity:
            print "##teamcity[testSuiteFinished name='pepa']"

        return success
