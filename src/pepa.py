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
from gittle import Gittle, GittleAuth
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

def expand_schema(types, schema):
    if isinstance(schema, dict):
        for entry in schema:
            if isinstance(schema[entry], dict) and 'type' in schema[entry]:
                if schema[entry]['type'] in types:
                    schema[entry].update(types[schema[entry]['type']])
            expand_schema(types, schema[entry])

# Get command line options
parser = optparse.OptionParser()
parser.add_option('-c', '--config', help='Configuration file', dest = 'config', action ='store', default = '/etc/pepa.conf')
parser.add_option('-d', '--debug', help='Print debug information', dest = 'debug', action ='store_true', default = False)
parser.add_option('-n', '--no-color', help='No color', dest = 'color', action ='store_false', default = True)
parser.add_option('-j', '--json', help='JSON output, instead of default YAML', dest = 'json', action ='store_true', default = False)
parser.add_option('-D', '--daemonize', help='Daemonize and run as a REST API', dest = 'daemonize', action ='store_true', default = False)
parser.add_option('--host', help='Hostname', dest = 'host', action ='store')
(opts, args) = parser.parse_args()

# Check that configuration file exist's
if not os.path.isfile(opts.config):
    error("Configuration file doesn't exist: %s" % opts.config)

# Check options
if opts.daemonize is False and not opts.host:
    error("You need to specify a host")
host = opts.host

# Get configuration
config = ConfigParser.ConfigParser()

# Set defaults
config.add_section('main')
config.set('main', 'basedir', '/srv/pepa')
config.set('main', 'backend', 'file')
config.set('main', 'environments', 'base')
config.add_section('http')
config.set('http', 'host', '127.0.0.1')
config.set('http', 'port', 5000)

# Get config
config.read([opts.config])
sequence = re.split('\s*,\s*', config.get('host', 'sequence'))
basedir = config.get('main', 'basedir')
backend = config.get('main', 'backend')
environments = re.split('\s*,\s*', config.get('main', 'environments'))
subdir = ''

schema = {}

# Check configuration
if backend != 'git' and backend != 'file':
    error('Unsupported backend needs to be "file" or "git"')

if backend == 'git':
    if not config.has_option('git', 'uri'):
        error('Need to set uri when using Git backend')
    uri = config.get('git', 'uri')

    if config.has_option('git', 'privkey'):
        privkey = config.get('git', 'privkey')
        key = open(privkey)
        auth = GittleAuth(key)

    envdir = basedir + '/base'
    if os.path.isdir(envdir):
        if opts.debug:
            info("Doing a Git pull for: %s in: %s" % (uri, envdir))
        repo = Gittle(envdir, uri)
        repo.pull()
    else:
        if opts.debug:
            info("Doing a Git clone for: %s to: %s" % (uri, envdir))
        repo = Gittle.clone(uri, envdir)

    branches = repo.branches
    del branches['master']
    for branch in branches.keys():
        envdir = basedir + '/' + branch
        if os.path.isdir(envdir + '/.git'):
            if opts.debug:
                info("Doing a Git pull for: %s in: %s" % (uri, envdir))
            repo = Gittle(envdir, uri)
            repo.pull()
        else:
            if opts.debug:
                info("Doing a Git clone for: %s to: %s" % (uri, envdir))
            repo = Gittle.clone(uri, envdir)
            repo.switch_branch(branch)

    environments = branches.keys()
    environments.append('base')

    if config.has_option('git', 'subdir'):
        subdir = config.get('git', 'subdir')

def get_schemas():
    schemadir = basedir + '/base/schemas'
    if not os.path.isdir(schemadir):
        error("Missing schema directory: %s" % schemadir)

    file = schemadir + '/types.json'
    if not os.path.isfile(file):
        error("Schema file doesn't exist: %s" % file)
    types_schema = json.load(open(file, 'r'))

    file = schemadir + '/input.json'
    if not os.path.isfile(file):
        error("Schema file doesn't exist: %s" % file)
    input_schema = json.load(open(file, 'r'))

    expand_schema(types_schema, input_schema)
    return input_schema

def get_config(host):
    # Load host input
    envdir = basedir + '/base' + '/' + subdir
    file = envdir + '/inputs/hosts/' + host + '.sls'
    if not os.path.isfile(file):
        error("Host is not defined: %s" % host)
    if opts.debug:
        info("Parsing input: %s" % file)
    input = yaml.load(open(file, 'r').read())
    input['default'] = 'default'

    env = input['environment']
    envdir = basedir + '/' + env + '/' + subdir

    # Load templates
    output = input
    for category in sequence:
        if category not in input:
            error("Input: %s is missing for host: %s" % (category, host))

        entries = []
        if type(input[category]) is list:
            entries = input[category]
        else:
            entries = [ input[category] ]

        for entry in entries:
            file = envdir + '/templates/' + category + '/' +  re.sub('\W', '_', entry.lower()) + '.sls'
            if os.path.isfile(file):
                if opts.debug:
                    info("Parsing template: %s" % file)
                template = Template(open(file).read())
                config = yaml.load(template.render(output))
                if config != None:
                    for key in config:
                        if opts.debug:
                            info2("Substituting key: %s" % key)
                        output[key] = config[key]
            else:
                if opts.debug:
                    warn("Template doesn't exist: %s" % file)
    return output

class Host(MethodView):
    def post(self):
        data = yaml.load(request.data)
        try:
            validate(data, schema['host'])
        except ValidationError as e:
            data['success'] = False
            data['error'] = e.message
            return yaml.safe_dump(data, indent = 4, default_flow_style = False), 400
        except SchemaError as e:
            data['success'] = False
            data['error'] = e.message
            return yaml.safe_dump(data, indent = 4, default_flow_style = False), 400

# Store data

        data['success'] = True
        return yaml.safe_dump(data, indent = 4, default_flow_style = False)

    def get(self):
        files = glob.glob(basedir + '/base/inputs/hosts/*.sls')
        hosts = {}
        for file in files:
            host = splitext(basename(file))[0]
            hosts[host] = get_config(host)
        return yaml.safe_dump(hosts, indent = 4, default_flow_style = False)

app.add_url_rule('/hosts', view_func = Host.as_view('hosts'))

class HostObject(MethodView):
    def get(self, host):
        output = get_config(host)
        return yaml.safe_dump(output, indent = 4, default_flow_style = False)

app.add_url_rule('/hosts/<host>', view_func = HostObject.as_view('host_object'))

if __name__ == '__main__' and opts.daemonize:
    schema = get_schemas()
    app.run(debug = True, host = config.get('http', 'host'), port = int(config.get('http', 'port')))
else:
    output = get_config(opts.host)
    if opts.json:
        print json.dumps(output, indent = 4) + '\n'
    else:
        print yaml.safe_dump(output, indent = 4, default_flow_style = False)
