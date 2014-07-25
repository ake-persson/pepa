#!/usr/bin/env python

import argparse
import json
import yaml
from os.path import isfile, join as makepath, splitext
from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError
from  glob import glob
import cobbler

COBBLER_USER='my service account'
COBBLER_PWD='my password'
COBBLER_HOST='my cobbler host'

# Convert key/value to nested dictionary
# Plundered with impunity from salt-pillar-dynamo (https://github.com/jasondenning/salt-pillar-dynamo)
def key_value_to_tree(data):
    tree = {}
    for flatkey, value in data.items():
        t = tree
        keys = flatkey.split('..')
        for key in keys:
            if key == keys[-1]:
                t[key] = value
            else:
                t = t.setdefault(key, {})
    return(tree)

# Validate resource using JSON schema
def validate_resource(fname, schema):
    print 'Validate file: %s' % fname
    resource = {}

    ext = splitext(fname)[1]
    if ext == '.yaml':
        resource = key_value_to_tree(yaml.load(open(fname).read()))
    elif ext == '.json':
        resource = key_value_to_tree(json.loads(open(fname).read()))
    else:
        print 'File needs to be either .yaml or .json: %s' % fname
        exit(1)

    # Validate resource
    try:
        validate(resource, schema)
    except ValidationError as e:
        print e.message
        exit(1)
    except SchemaError as e:
        print e.message
        exit(1)

    if args.cobbler and not args.all:
        create_cobbler_system(resource)

def create_cobbler_system(host):
    print 'Create Cobbler system: %s' % host['hostname']

    system = cobbler.CobblerSystem(host['hostname'], host['hostname'], host['cobbler']['profile'],
        host['network']['gateway'], 'eth0', host['network']['interfaces']['eth0']['hwaddr'],
        host['network']['interfaces']['eth0']['ipv4'], host['network']['interfaces']['eth0']['netmask'])

    # Create system on Cobbler
    cd = cobbler.Cobbler(COBBLER_HOST, COBBLER_USER, COBBLER_PWD)
    cd.connect()
    cd.login()
    name = cd.find_by_hostname(host['hostname'])
    if name:
        cd.remove_system(name[0])
    name = cd.find_by_hwaddr(host['network']['interfaces']['eth0']['hwaddr'])
    if name:
        cd.remove_system(name[0])
    cd.create_system(system)

# Get command line options
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', help = 'Print debug information', action = 'store_true', default = False)
parser.add_argument('-b', '--basedir', help = 'Base directory', required = True)
parser.add_argument('-r', '--resource', help = 'Resource, defaults to hosts', default = 'hosts')
parser.add_argument('-f', '--file', help = 'Validate resource file')
parser.add_argument('-a', '--all', help = 'Validate all resource files', action = 'store_true', default = False)
parser.add_argument('-c', '--cobbler', help = 'Create Cobbler system, can\'t be used with -a', action = 'store_true', default = False)
args = parser.parse_args()

# Load resource schema
fname = makepath(args.basedir, args.resource, 'schema')
schema = dict()

if isfile(fname + '.yaml'):
    schema = yaml.load(open(fname + '.yaml').read())
elif isfile(fname + '.json'):
    schema = json.loads(open(fname + '.json').read())
else:
    print 'Schema doesn\'t exist: %s.(json|yaml)' % fname

# Validate resource files
if args.all:
    files = glob(makepath(args.basedir, args.resource, 'inputs', '*'))
    for fname in files:
        validate_resource(fname, schema)
else:
    validate_resource(args.file, schema)
