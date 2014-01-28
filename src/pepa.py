#!/usr/bin/env python

import ConfigParser
import argparse
import json
import yaml
import os
import sys
import re
import jinja2
from termcolor import colored
import types
import glob
import flask
from flask.views import MethodView, request
from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError

def error(message):
    if args.color:
        print >> sys.stderr, colored('[ ERROR ] ' + message, 'red')
    else:
        print >> sys.stderr, '[ ERROR ] ' + message
    sys.exit(1)

def warn(message):
    if args.color:
        print >> sys.stderr, colored('[ WARN ] ' + message, 'yellow')
    else:
        print >> sys.stderr, '[ WARN ] ' + message

def info(message):
    if args.color:
        print >> sys.stderr, colored('[ INFO ] ' + message, 'green')
    else:
        print >> sys.stderr, '[ INFO ] ' + message

def info2(message):
    if args.color:
        print >> sys.stderr, colored('[ INFO ] ' + message, 'cyan')
    else:
        print >> sys.stderr, '[ INFO ] ' + message

def get_config(resource, key):
    fn = os.path.join(basedir, 'base', resource, 'inputs', key + '.yaml')
    if not os.path.isfile(fn):
        error("Resource is not defined: %s" % key)
    if args.debug:
        info("Parsing input: %s" % fn)

    # Parse both YAML and JSON based on file extension
    input = yaml.load(open(fn, 'r').read())
    input['default'] = 'default'
    input['environment'] = 'base'

    envdir = os.path.join(basedir, input['environment'])

    # Load templates
    output = input
    for category in sequences[resource]:
        if category not in input:
            continue

        entries = []
        if type(input[category]) is list:
            entries = input[category]
        else:
            entries = [ input[category] ]

        for entry in entries:
            fn = os.path.join(envdir, resource, 'templates', category, re.sub('\W', '_', entry.lower()) + '.yaml')
            if os.path.isfile(fn):
                if args.debug:
                    info("Parsing template: %s" % fn)
                template = jinja2.Template(open(fn).read())
                config = yaml.load(template.render(output))
                if config != None:
                    for key in config:
                        if args.debug:
                            info2("Substituting key: %s" % key)
                        output[key] = config[key]
            else:
                if args.debug:
                    warn("Template doesn't exist: %s" % fn)
    return output

# Get command line options
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help = 'Configuration file', default = '/etc/pepa.conf')
parser.add_argument('-d', '--debug', help = 'Print debug information', action = 'store_true', default = False)
parser.add_argument('-n', '--no-color', help = 'No color', dest = 'color', action = 'store_false', default = True)
parser.add_argument('-j', '--json', help = 'JSON output, instead of default YAML', action = 'store_true', default = False)
parser.add_argument('-D', '--daemonize', help = 'Daemonize and run as a REST API', action = 'store_true', default = False)
parser.add_argument('-r', '--resource', help = 'Resource')
parser.add_argument('-k', '--key', help = 'Resource key')
args = parser.parse_args()

# Check that configuration file exist's
if not os.path.isfile(args.config):
    error("Configuration file doesn't exist: %s" % args.config)

# Check options
if args.daemonize is False and not args.resource:
    error("You need to specify a resource")

# Get configuration
config = ConfigParser.ConfigParser()

# Set defaults
config.add_section('main')
config.set('main', 'basedir', '/srv/pepa')
config.set('main', 'backend', 'file')
config.set('main', 'environments', 'base')
config.set('main', 'resources', 'hosts')
config.add_section('hosts')
config.set('hosts', 'key', 'hostname')
config.set('hosts', 'sequence', 'default, environment, region, country, roles, hostname')
config.add_section('http')
config.set('http', 'host', '127.0.0.1')
config.set('http', 'port', 5000)

# Get config
config.read([args.config])
basedir = config.get('main', 'basedir')
backend = config.get('main', 'backend')
environments = re.split('\s*,\s*', config.get('main', 'environments'))
resources = re.split('\s*,\s*', config.get('main', 'resources'))
sequences = {}
schemas = {}
for resource in resources:
# Check that sequence exist
# Check that key exist
    sequences[resource] = re.split('\s*,\s*', config.get(resource, 'sequence'))
    fn = os.path.join(basedir, 'base', resource, 'schema.json')
    if not os.path.isfile(fn):
        error("JSON schema file doesn't exist: %s" % fn)
# Validate JSON Schema
    schemas[resource] = json.load(open(fn, 'r'))

if backend != 'file':
    error('Unsupported backend: %s' % backend)

app = flask.Flask(__name__)

class Resource(MethodView):
    def get(self, resource):
        files = glob.glob(os.path.join(basedir, 'base', resource, 'inputs', '*.yaml'))
        results = {}
        for file in files:
            key = os.path.splitext(os.path.basename(file))[0]
            # Key shouldn't be based on filename but rather on the entry in the file
            results[key] = get_config(resource, key)
        return yaml.safe_dump(results, indent = 4, default_flow_style = False)

app.add_url_rule('/<resource>', view_func = Resource.as_view('resource'))

class ResourceEntry(MethodView):
    def get(self, resource, key):
        return yaml.safe_dump(get_config(resource, key), indent = 4, default_flow_style = False)

app.add_url_rule('/<resource>/<key>', view_func = ResourceEntry.as_view('resource_entry'))

if __name__ == '__main__' and args.daemonize:
    app.run(debug = True, host = config.get('http', 'host'), port = int(config.get('http', 'port')))
else:
    output = get_config(args.resource, args.key)
    if args.json:
        print json.dumps(output, indent = 4) + '\n'
    else:
        print yaml.safe_dump(output, indent = 4, default_flow_style = False)