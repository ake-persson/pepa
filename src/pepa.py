#!/usr/bin/env python

import ConfigParser
import argparse
import json
import yaml
from os.path import isfile, join as makepath, splitext, basename
import sys
from sys import stderr
import re
import jinja2
from termcolor import colored
import types
from  glob import glob
import flask
from flask import request, Response
import mimerender
from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError
import ldap
from flask.ext.httpauth import HTTPBasicAuth

def notify(message, color = 'red', prepend = ''):
    if args.color:
        print >> stderr, colored(prepend + message, color)
    else:
        print >> stderr, prepend + message

def error(message, color = 'red'):
    notify(message, color, '[ ERRO ] ')
    sys.exit(1)

def warn(message, color = 'magenta'):
    if args.debug:
        notify(message, color, '[ WARN ] ')

def info(message, color = 'green'):
    if args.debug:
        notify(message, color, '[ INFO ] ')

def get_config(resource, key):
    input = {
        'default': 'default',
        'environment': 'base',
    }

    fn = makepath(basedir, 'base', resource, 'inputs', key)
    if isfile(fn + '.yaml'):
        info("Load resource: %s.json" % fn)
        input.update(yaml.load(open(fn + '.yaml').read()))
    elif isfile(fn + '.json'):
        info("Load resource: %s.json" % fn)
        input.update(json.loads(open(fn + '.json').read()))
    else:
        error("Resource doesn't exist: %s.(json|yaml)" % fn)

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
            config = None
            fn = makepath(basedir,  input['environment'], resource, 'templates', category,
                re.sub('\W', '_', entry.lower()))
            if isfile(fn + '.yaml'):
                info("Load template: %s.yaml" % fn)
                template = jinja2.Template(open(fn + '.yaml').read())
                config = yaml.load(template.render(output))
            elif isfile(fn + '.json'):
                info("Load template: %s.json" % fn)
                template = jinja2.Template(open(fn + '.yaml').read())
                config = json.loads(template.render(output))
            else:
                warn("Template doesn't exist: %s.(json|yaml)" % fn)
                continue

            if config != None:
                for key in config:
                    info("Substituting key: %s" % key, 'yellow')
                    output[key] = config[key]
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
if not isfile(args.config):
    error("Configuration file doesn't exist: %s" % args.config)

# Check options
if args.daemonize is False and not args.resource:
    error("You need to specify a resource")

# Get configuration
config = ConfigParser.ConfigParser()

# Set defaults
config.add_section('main')
config.set('main', 'basedir', '/srv/pepa')
config.set('main', 'environments', 'base')
config.set('main', 'resources', 'hosts, schemas')
config.add_section('hosts')
config.set('hosts', 'key', 'hostname')
config.set('hosts', 'sequence', 'default, environment, region, country, roles, hostname')
config.add_section('schemas')
config.set('schemas', 'key', 'schema')
config.set('schemas', 'sequence', 'default')
config.add_section('http')
config.set('http', 'host', '127.0.0.1')
config.set('http', 'port', 8080)
config.set('main', 'auth', 'ad')

# Get config
config.read([args.config])
basedir = config.get('main', 'basedir')
environments = re.split('\s*,\s*', config.get('main', 'environments'))
resources = re.split('\s*,\s*', config.get('main', 'resources'))
sequences = {}
schemas = {}
for resource in resources:
    if not config.has_option(resource, 'key'):
        error("There is no key configured for resource: %s" % resource)
    if not config.has_option(resource, 'sequence'):
        error("There is no sequence configured for resource: %s" % resource)
    sequences[resource] = re.split('\s*,\s*', config.get(resource, 'sequence'))

    fn = makepath(basedir, 'base/schemas/inputs', resource)
    if isfile(fn + '.yaml'):
        info("Load schema: %s.yaml" % fn)
        schemas[resource] = yaml.load(open(fn + '.yaml').read())
    elif isfile(fn + '.json'):
        info("Load schema: %s.json" % fn)
        schemas[resource] = json.loads(open(fn + '.json').read())
    else:
        error("Schema doesn't exist: %s.(json|yaml)" % fn)

if not args.daemonize:
    output = get_config(args.resource, args.key)
    if args.json:
        print json.dumps(output, indent = 4) + '\n'
    else:
        print yaml.safe_dump(output, indent = 4, default_flow_style = False)
    sys.exit(0)

app = flask.Flask(__name__)
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    ld = ldap.initialize('ldaps://' + config.get('ad', 'server'))
    ld.set_option(ldap.OPT_X_TLS_DEMAND, True)
    try:
        ld.simple_bind_s(config.get('ad', 'domain') + '\\' + username, password)
        return True
    except:
        return False

mimerender = mimerender.FlaskMimeRender()
render_json = lambda **args: json.dumps(args, indent = 4)
render_yaml = lambda **args: yaml.safe_dump(args, indent = 4, default_flow_style = False)

@app.route('/<resource>', methods=["GET"])
@mimerender(
    default = 'yaml',
    yaml  = render_yaml,
    json = render_json
)
def get_all_resources(resource):
    files = glob(makepath(basedir, 'base', resource, 'inputs', '*'))
    output = {}
    for file in files:
        key = splitext(basename(file))[0]
        output[key] = get_config(resource, key)
    return output

@app.route('/<resource>', methods=["POST"])
@auth.login_required
@mimerender(
    default = 'yaml',
    yaml  = render_yaml,
    json = render_json
)
def new_resource(resource):
    data = {}
    if request.accept_mimetypes == 'application/json':
        data = json.loads(request.data)
    else:
        data = yaml.load(request.data)

    try:
        validate(data, schemas[resource])
    except ValidationError as e:
        data['success'] = False
        data['error'] = e.message
        return data, 400
    except SchemaError as e:
        data['success'] = False
        data['error'] = e.message
        return data, 400

    fn = makepath(basedir, 'base', resource, 'inputs', data[config.get(resource, 'key')])
    if isfile(fn + '.json'):
        os.unlink(fn + '.json')

    f = open(fn + '.yaml', 'w')
    f.write(yaml.safe_dump(data, indent = 4, default_flow_style = False))
    f.close()

    data['success'] = True
    return data

@app.route('/<resource>/<key>', methods=["PATCH"])
@auth.login_required
@mimerender(
    default = 'yaml',
    yaml  = render_yaml,
    json = render_json
)
def modify_resource(resource, key):
    data = {}

    fn = makepath(basedir, 'base', resource, 'inputs', key)
    if isfile(fn + '.yaml'):
        info("Load resource input: %s" % fn)
        data = yaml.load(open(fn + '.yaml', 'r'))
    elif isfile(fn + '.json'):
        info("Load resource input: %s" % fn)
        data = json.loads(open(fn + '.json', 'r'))

    if request.accept_mimetypes == 'application/json':
        data.update(json.loads(request.data))
    else:
        data.update(yaml.load(request.data))

    try:
        validate(data, schemas[resource])
    except ValidationError as e:
        data['success'] = False
        data['error'] = e.message
        return data, 400
    except SchemaError as e:
        data['success'] = False
        data['error'] = e.message
        return data, 400

    if isfile(fn + '.yaml'):
        f = open(fn + '.yaml', 'w')
        f.write(yaml.safe_dump(data, indent = 4, default_flow_style = False))
        f.close()
    elif isfile(fn + '.json'):
        f = open(fn + '.json', 'w')
        f.write(json.dumps(data, indent = 4))
        f.close()

    data['success'] = True
    return data

@app.route('/<resource>/<key>', methods=["GET"])
@mimerender(
    default = 'yaml',
    yaml  = render_yaml,
    json = render_json
)
def get_resource(resource, key):
# get_config does sys.exit on missing resource, needs to raise an exception
    data = get_config(resource, key)
    return data

if __name__ == '__main__':
    app.run(debug = True, host = config.get('http', 'host'), port = int(config.get('http', 'port')))