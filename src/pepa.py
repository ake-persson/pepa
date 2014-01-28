#!/usr/bin/env python

import json
import yaml
import os
import sys
import re
from jinja2 import Template
import ConfigParser
import optparse
from termcolor import colored
import types
import glob
from os.path import basename, splitext
import flask
from flask.views import MethodView, request
from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError

app = flask.Flask(__name__)

global opts
global config

def error(message):
    if opts.color:
        print >> sys.stderr, colored('[ ERROR ] ' + message, 'red')
    else:
        print >> sys.stderr, '[ ERROR ] ' + message
    sys.exit(1)

def warn(message):
    if opts.color:
        print >> sys.stderr, colored('[ WARN ] ' + message, 'yellow')
    else:
        print >> sys.stderr, '[ WARN ] ' + message

def info(message):
    if opts.color:
        print >> sys.stderr, colored('[ INFO ] ' + message, 'green')
    else:
        print >> sys.stderr, '[ INFO ] ' + message

def info2(message):
    if opts.color:
        print >> sys.stderr, colored('[ INFO ] ' + message, 'cyan')
    else:
        print >> sys.stderr, '[ INFO ] ' + message

# Get command line options
parser = optparse.OptionParser()
parser.add_option('-c', '--config', help='Configuration file', dest = 'config', action ='store', default = '/etc/pepa.conf')
parser.add_option('-d', '--debug', help='Print debug information', dest = 'debug', action ='store_true', default = False)
parser.add_option('-n', '--no-color', help='No color', dest = 'color', action ='store_false', default = True)
parser.add_option('-j', '--json', help='JSON output, instead of default YAML', dest = 'json', action ='store_true', default = False)
parser.add_option('-D', '--daemonize', help='Daemonize and run as a REST API', dest = 'daemonize', action ='store_true', default = False)
parser.add_option('-r', '--resource', help='Resource', dest = 'resource', action ='store')
parser.add_option('-k', '--key', help='Resource key', dest = 'key', action ='store')
(opts, args) = parser.parse_args()

# Check that configuration file exist's
if not os.path.isfile(opts.config):
    error("Configuration file doesn't exist: %s" % opts.config)

# Check options
if opts.daemonize is False and not opts.resource:
    error("You need to specify a resource")

# Get configuration
config = ConfigParser.ConfigParser()

# Set defaults
config.add_section('main')
config.set('main', 'basedir', '/srv/pepa')
config.set('main', 'backend', 'file')
config.set('main', 'environments', 'base')
config.set('main', 'resources', 'hosts')
config.add_section('http')
config.set('http', 'host', '127.0.0.1')
config.set('http', 'port', 5000)

# Get config
config.read([opts.config])
# Check that item exist's to avoid error
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
    schemas[resource] = json.load(open(fn, 'r'))

# Check configuration
if backend != 'file':
    error('Unsupported backend: %s' % backend)

def get_config(resource, key):

    fn = os.path.join(basedir, 'base', resource, 'inputs', key + '.yaml')
    if not os.path.isfile(fn):
        error("Resource is not defined: %s" % key)
    if opts.debug:
        info("Parsing input: %s" % fn)

    # Parse both YAML and JSON based on file extension
    input = yaml.load(open(fn, 'r').read())
    input['default'] = 'default'
    input['environment'] = 'base'

    # Check environment is defined, otherwise default to 'base'
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
                if opts.debug:
                    info("Parsing template: %s" % fn)
                template = Template(open(fn).read())
                config = yaml.load(template.render(output))
                if config != None:
                    for key in config:
                        if opts.debug:
                            info2("Substituting key: %s" % key)
                        output[key] = config[key]
            else:
                if opts.debug:
                    warn("Template doesn't exist: %s" % fn)
    return output

class Resource(MethodView):
    def get(self, resource):
        print resource
        files = glob.glob(os.path.join(basedir, 'base', resource, 'inputs', '*.yaml'))
        results = {}
        for file in files:
            key = splitext(basename(file))[0]
            results[key] = get_config(resource, key)
        return yaml.safe_dump(results, indent = 4, default_flow_style = False)

app.add_url_rule('/<resource>', view_func = Resource.as_view('resource'))

if __name__ == '__main__' and opts.daemonize:
    app.run(debug = True, host = config.get('http', 'host'), port = int(config.get('http', 'port')))
else:
    output = get_config(opts.resource, opts.key)
    if opts.json:
        print json.dumps(output, indent = 4) + '\n'
    else:
        print yaml.safe_dump(output, indent = 4, default_flow_style = False)
