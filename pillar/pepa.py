#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
'''
Pepa
====

Configuration templating for SaltStack using Hierarchical substitution and Jinja.

Configuring Pepa
================

.. code-block:: yaml

    extension_modules: /srv/salt/ext

    ext_pillar:
      - pepa:
          resource: host                # Name of resource directory and sub-key in pillars
          sequence:                     # Sequence used for hierarchical substitution
            - hostname:                 # Name of key
                name: input             # Alias used for template directory
                base_only: True         # Only use templates from Base environment, i.e. no staging
            - default:
            - environment:
            - location..region:
                name: region
            - location..country:
                name: country
            - location..datacenter:
                name: datacenter
            - roles:
            - osfinger:
                name: os
            - hostname:
                name: override
                base_only: True
          subkey: True                  # Create a sub-key in pillars, named after the resource in this case [host]
          subkey_only: True             # Only create a sub-key, and leave the top level untouched

    pepa_roots:                         # Base directory for each environment
      base: /srv/pepa/base              # Path for base environment
      dev: /srv/pepa/base               # Associate dev with base
      qa: /srv/pepa/qa
      prod: /srv/pepa/prod

    # Use a different delimiter for nested dictionaries, defaults to '..' since some keys may use '.' in the name
    #pepa_delimiter: ..

    # Supply Grains for Pepa, this should **ONLY** be used for testing or validation
    #pepa_grains:
    #  environment: dev

    # Supply Pillar for Pepa, this should **ONLY** be used for testing or validation
    #pepa_pillars:
    #  saltversion: 0.17.4

    # Enable debug for Pepa, and keep Salt on warning
    #log_level: debug

    #log_granular_levels:
    #  salt: warning
    #  salt.loaded.ext.pillar.pepa: debug

Pepa can also be used in Master-less SaltStack setup.

Templates
=========

Templates is configuration for a host or software, that can use information from Grains or Pillars. These can then be used for hierarchically substitution.

**Example File:** host/input/test_example_com.yaml

.. code-block:: yaml

    location..region: emea
    location..country: nl
    location..datacenter: foobar
    environment: dev
    roles:
      - salt.master
    network..gateway: 10.0.0.254
    network..interfaces..eth0..hwaddr: 00:20:26:a1:12:12
    network..interfaces..eth0..dhcp: False
    network..interfaces..eth0..ipv4: 10.0.0.3
    network..interfaces..eth0..netmask: 255.255.255.0
    network..interfaces..eth0..fqdn: {{ hostname }}
    cobbler..profile: fedora-19-x86_64

As you see in this example you can use Jinja directly inside the template.

**Example File:** host/region/amer.yaml

.. code-block:: yaml

    network..dns..servers:
      - 10.0.0.1
      - 10.0.0.2
    time..ntp..servers:
      - ntp1.amer.example.com
      - ntp2.amer.example.com
      - ntp3.amer.example.com
    time..timezone: America/Chihuahua
    yum..mirror: yum.amer.example.com

Each template is named after the value of the key using lowercase and all extended characters are replaced with underscore.

**Example:**

osfinger: Fedora-19

**Would become:**

fedora_19.yaml

Nested dictionaries
===================

In order to create nested dictionaries as output you can use double dot **".."** as a delimiter. You can change this using "pepa_delimiter" we choose double dot since single dot is already used by key names in some modules, and using ":" requires quoting in the YAML.

**Example:**

.. code-block:: yaml

    network..dns..servers:
      - 10.0.0.1
      - 10.0.0.2
    network..dns..options:
      - timeout:2
      - attempts:1
      - ndots:1
    network..dns..search:
      - example.com

**Would become:**

.. code-block:: yaml

    network:
      dns:
        servers:
          - 10.0.0.1
          - 10.0.0.2
        options:
          - timeout:2
          - attempts:1
          - ndots:1
        search:
          - example.com

Operators
=========

Operators can be used to merge/unset a list/hash or set the key as immutable, so it can't be changed.

=========== ================================================
Operator    Description
=========== ================================================
merge()     Merge list or hash
unset()     Unset key
immutable() Set the key as immutable, so it can't be changed
imerge()    Set immutable and merge
iunset()    Set immutable and unset
=========== ================================================

**Example:**

.. code-block:: yaml

    network..dns..search..merge():
      - foobar.com
      - dummy.nl
    owner..immutable(): Operations
    host..printers..unset():

Links
=====

For more examples and information see <https://github.com/mickep76/pepa>.
'''

__author__ = 'Michael Persson <michael.ake.persson@gmail.com>'
__author_email__ = 'michael.ake.persson@gmail.com'
__copyright__ = 'Copyright (c) 2013 Michael Persson'
__license__ = 'Apache License, Version 2.0'
__version__ = '0.7.6'
__url__ = 'https://github.com/mickep76/pepa.git'

# Import python libs
import logging
import sys
import glob
import yaml
import jinja2
import re
from os.path import isfile, join

# Options
__opts__ = {
    'pepa_roots': {
        'base': '/srv/salt'
    },
    'pepa_delimiter': '..',
    'pepa_validate': False
}

# Set up logging
log = logging.getLogger(__name__)


def key_value_to_tree(data):
    '''
    Convert key/value to tree
    '''
    tree = {}
    for flatkey, value in data.items():
        t = tree
        keys = flatkey.split(__opts__['pepa_delimiter'])
        for key in keys:
            if key == keys[-1]:
                t[key] = value
            else:
                t = t.setdefault(key, {})
    return tree


def ext_pillar(minion_id, pillar, resource, sequence, subkey=False, subkey_only=False):
    '''
    Evaluate Pepa templates
    '''
    roots = __opts__['pepa_roots']

    # Default input
    inp = {}
    inp['default'] = 'default'
    inp['hostname'] = minion_id

    if 'environment' in pillar:
        inp['environment'] = pillar['environment']
    elif 'environment' in __grains__:
        inp['environment'] = __grains__['environment']
    else:
        inp['environment'] = 'base'

    # Load templates
    output = inp
    output['pepa_templates'] = []
    immutable = {}

    for categ, info in [s.items()[0] for s in sequence]:
        if categ not in inp:
            log.warn("Category is not defined: {0}".format(categ))
            continue

        alias = None
        if isinstance(info, dict) and 'name' in info:
            alias = info['name']
        else:
            alias = categ

        templdir = None
        if info and 'base_only' in info and info['base_only']:
            templdir = join(roots['base'], resource, alias)
        else:
            templdir = join(roots[inp['environment']], resource, alias)

        entries = []
        if isinstance(inp[categ], list):
            entries = inp[categ]
        elif not inp[categ]:
            log.warn("Category has no value set: {0}".format(categ))
            continue
        else:
            entries = [inp[categ]]

        for entry in entries:
            results_jinja = None
            results = None
            fn = join(templdir, re.sub(r'\W', '_', entry.lower()) + '.yaml')
            if isfile(fn):
                log.info("Loading template: {0}".format(fn))
                template = jinja2.Template(open(fn).read())
                output['pepa_templates'].append(fn)

                try:
                    data = key_value_to_tree(output)
                    data['grains'] = __grains__.copy()
                    data['pillar'] = pillar.copy()
                    results_jinja = template.render(data)
                    results = yaml.load(results_jinja)
                except jinja2.UndefinedError, err:
                    log.error('Failed to parse JINJA template: {0}\n{1}'.format(fn, err))
                except yaml.YAMLError, err:
                    log.error('Failed to parse YAML in template: {0}\n{1}'.format(fn, err))
            else:
                log.info("Template doesn't exist: {0}".format(fn))
                continue

            if results is not None:
                for key in results:
                    skey = key.rsplit(__opts__['pepa_delimiter'], 1)
                    rkey = None
                    operator = None
                    if len(skey) > 1 and key.rfind('()') > 0:
                        rkey = skey[0].rstrip(__opts__['pepa_delimiter'])
                        operator = skey[1]

                    if key in immutable:
                        log.warning('Key {0} is immutable, changes are not allowed'.format(key))
                    elif rkey in immutable:
                        log.warning("Key {0} is immutable, changes are not allowed".format(rkey))
                    elif operator == 'merge()' or operator == 'imerge()':
                        if operator == 'merge()':
                            log.debug("Merge key {0}: {1}".format(rkey, results[key]))
                        else:
                            log.debug("Set immutable and merge key {0}: {1}".format(rkey, results[key]))
                            immutable[rkey] = True
                        if rkey not in output:
                            log.error('Cant\'t merge key {0} doesn\'t exist'.format(rkey))
                        elif type(results[key]) != type(output[rkey]):
                            log.error('Can\'t merge different types for key {0}'.format(rkey))
                        elif type(results[key]) is dict:
                            output[rkey].update(results[key])
                        elif type(results[key]) is list:
                            output[rkey].extend(results[key])
                        else:
                            log.error('Unsupported type need to be list or dict for key {0}'.format(rkey))
                    elif operator == 'unset()' or operator == 'iunset()':
                        if operator == 'unset()':
                            log.debug("Unset key {0}".format(rkey))
                        else:
                            log.debug("Set immutable and unset key {0}".format(rkey))
                            immutable[rkey] = True
                        if rkey in output:
                            del output[rkey]
                    elif operator == 'immutable()':
                        log.debug("Set immutable and substitute key {0}: {1}".format(rkey, results[key]))
                        immutable[rkey] = True
                        output[rkey] = results[key]
                    elif operator is not None:
                        log.error('Unsupported operator {0}, skipping key {1}'.format(operator, rkey))
                    else:
                        log.debug("Substitute key {0}: {1}".format(key, results[key]))
                        output[key] = results[key]

    tree = key_value_to_tree(output)
    pillar_data = {}
    if subkey_only:
        pillar_data[resource] = tree.copy()
    elif subkey:
        pillar_data = tree
        pillar_data[resource] = tree.copy()
    else:
        pillar_data = tree
    if __opts__['pepa_validate']:
        pillar_data['pepa_keys'] = output.copy()
    return pillar_data
