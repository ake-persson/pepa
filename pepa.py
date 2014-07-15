__author__ = 'Michael Persson <michael.ake.persson@gmail.com>'
__copyright__ = 'Copyright (c) 2013 Michael Persson'
__license__ = 'GPLv3'
__version__ = '0.6.2'

# Import python libs
from salt.exceptions import SaltInvocationError
import logging

# Set up logging
log = logging.getLogger(__name__)

# Name
__virtualname__ = 'pepa'

# Options
__opts__ = {
    'pepa_roots': {
        'base': '/srv/salt'
    },
    'pepa_delimiter': '..'
}

# Import libraries
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from os.path import isfile, join
    HAS_OS_PATH = True
except ImportError:
    HAS_OS_PATH = False

try:
    import re
    HAS_RE = True
except ImportError:
    HAS_RE = False

try:
    import jinja2
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

def __virtual__():
    if not HAS_YAML:
        log.error('Failed to load "yaml" library')
        return False

    if not HAS_OS_PATH:
        log.error('Failed to load "os.path" library')
        return False

    if not HAS_RE:
        log.error('Failed to load "re" library')
        return False

    if not HAS_JINJA2:
        log.error('Failed to load "jinja2" library')
        return False

    return(__virtualname__)

# Convert key/value to tree
def key_value_to_tree(data):
    tree = {}
    for flatkey, value in data.items():
        t = tree
        keys = flatkey.split(__opts__['pepa_delimiter'])
        for key in keys:
            if key == keys[-1]:
                t[key] = value
            else:
                t = t.setdefault(key, {})
    return(tree)

def ext_pillar(minion_id, pillar, resource, sequence):
    roots = __opts__['pepa_roots']

    # Default input
    input = {}
    input['default'] = 'default'
    input['hostname'] = minion_id
    if 'environment' in __grains__:
        input['environment'] = __grains__['environment']
    else:
        input['environment'] = 'base'

    # Load templates
    output = input
    output['pepa_templates'] = []

    for name, info in [s.items()[0] for s in sequence]:

        if name not in input:
            continue

        alias = None
        if type(info) is dict and 'name' in info:
            alias = info['name']
        else:
            alias = name

        templdir = None
        if info and 'base_only' in info and info['base_only']:
            templdir = join(roots['base'], resource, alias)
        else:
            templdir = join(roots[input['environment']], resource, alias)

        entries = []
        if type(input[name]) is list:
            entries = input[name]
        else:
            entries = [ input[name] ]

        for entry in entries:
            results = None
            fn = join(templdir, re.sub('\W', '_', entry.lower()) + '.yaml')
            if isfile(fn):
                log.debug("Loading template: %s" % fn)
                template = jinja2.Template(open(fn).read())
                output['pepa_templates'].append(fn)
                data = key_value_to_tree(output)
                data['grains'] = __grains__.copy()
                data['pillar'] = pillar.copy()
                results = yaml.load(template.render(data))
            else:
                log.debug("Template doesn't exist: %s" % fn)
                continue

            if results != None:
                for key in results:
                    log.debug("Substituting key: %s value: %s" % (key, results[key]))
                    output[key] = results[key]

    tree = key_value_to_tree(output)
    pillar_data = tree
    pillar_data['pepa'] = tree.copy()
    return pillar_data
