#!/usr/bin/env python

import ConfigParser
import argparse
import json
import yaml
from os import unlink
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
from OpenSSL import SSL
import pymongo
from bson.objectid import ObjectId
import time

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

    if config.get('main', 'backend') == 'file' or resource == 'schemas':
        fn = makepath(basedir, 'base', resource, 'inputs', key)
        if isfile(fn + '.yaml'):
            info("Load resource: %s.json" % fn)
            input.update(yaml.load(open(fn + '.yaml').read()))
        elif isfile(fn + '.json'):
            info("Load resource: %s.json" % fn)
            input.update(json.loads(open(fn + '.json').read()))
        else:
            error("Resource doesn't exist: %s.(json|yaml)" % fn)
    else:
        input.update(dbo[resource].find_one({ config.get(resource, 'key'): key }))
        del input['_id']

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
            results = None
            fn = makepath(basedir,  input['environment'], resource, 'templates', category,
                re.sub('\W', '_', entry.lower()))
            if isfile(fn + '.yaml'):
                info("Load template: %s.yaml" % fn)
                template = jinja2.Template(open(fn + '.yaml').read())
                results = yaml.load(template.render(output))
            elif isfile(fn + '.json'):
                info("Load template: %s.json" % fn)
                template = jinja2.Template(open(fn + '.yaml').read())
                results = json.loads(template.render(output))
            else:
                warn("Template doesn't exist: %s.(json|yaml)" % fn)
                continue

            if results != None:
                for key in results:
                    info("Substituting key: %s" % key, 'yellow')
                    output[key] = results[key]
    return output

# Get command line options
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help = 'Configuration file', default = '/etc/pepa/pepa.conf')
parser.add_argument('-d', '--debug', help = 'Print debug information', action = 'store_true', default = False)
parser.add_argument('-n', '--no-color', help = 'No color', dest = 'color', action = 'store_false', default = True)
parser.add_argument('-j', '--json', help = 'JSON output, instead of default YAML', action = 'store_true', default = False)
parser.add_argument('-D', '--dont-daemonize', help = 'Don\'t daemonize and run as a REST API', action = 'store_false', default = True)
parser.add_argument('-r', '--resource', help = 'Resource')
parser.add_argument('-k', '--key', help = 'Resource key')
args = parser.parse_args()

# Check that configuration file exist's
if not isfile(args.config):
    error("Configuration file doesn't exist: %s" % args.config)

# Check options
if args.dont_daemonize is False and not args.resource:
    error("You need to specify a resource")

# Get configuration
config = ConfigParser.ConfigParser()

# Set defaults
config.add_section('main')
config.set('main', 'basedir', '/srv/pepa')
config.set('main', 'environments', 'base')
config.set('main', 'resources', 'hosts, schemas')
config.set('main', 'backend', 'file')
config.set('main', 'auth', 'ad')
config.set('main', 'require_auth', 'POST, PATCH, DELETE')
config.set('main', 'user', 'pepa')
config.set('main', 'group', 'pepa')
config.add_section('hosts')
config.set('hosts', 'key', 'hostname')
config.set('hosts', 'sequence', 'default, environment, region, country, roles, hostname')
config.add_section('schemas')
config.set('schemas', 'key', 'schema')
config.set('schemas', 'sequence', 'default')
config.add_section('http')
config.set('http', 'host', '127.0.0.1')
config.set('http', 'port', '8080')
config.set('http', 'use_ssl', 'false')
config.set('http', 'ssl_pkey', '/etc/pepa/ssl/server.key')
config.set('http', 'ssl_cert', '/etc/pepa/ssl/server.crt')
config.add_section('mongodb')
config.set('mongodb', 'server', '127.0.0.1')
config.set('mongodb', 'port', '27017')
config.set('mongodb', 'database', 'pepa')
config.set('mongodb', 'connect_retry', '6')
config.set('mongodb', 'connect_wait', '30')

# Get config
config.read([args.config])
basedir = config.get('main', 'basedir')
environments = re.split('\s*,\s*', config.get('main', 'environments'))
resources = re.split('\s*,\s*', config.get('main', 'resources'))
require_auth = re.split('\s*,\s*', config.get('main', 'require_auth'))
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

# Get user and group id
uid = getpwnam(config.get('main', 'user')).pw_uid
gid = getgrnam(config.get('main', 'group')).gr_gid

# If root then switch user and group
if os.getuid() == 0:
    os.setuid(uid)
if os.getgid() == 0:
    os.setgid(gid)

# Check that we're running as the correct user and group
if os.getuid() != uid:
    error('Application need to run as user: %s(%s)' % (config.get('main', 'user'), uid))
if os.getgid() != gid:
    error('Application need to run as group: %s(%s)' % (config.get('main', 'group'), gid))

# Initiate MongoDB
database =  None
conn = None
dbo = None
if config.get('main', 'backend') == 'mongodb':
    database = config.get('mongodb', 'database')
    info('Using MongoDB backend with database: %s' % database)
    connection_ok = False
    for attempt in range(1, config.getint('mongodb', 'connect_retry')):
        try:
            conn = pymongo.Connection(config.get('mongodb', 'server'), config.getint('mongodb', 'port'))
            dbo = conn[database]
            connection_ok = True
            break
        except:
            warn('Failed to connect to MongoDB waiting %s seconds, %s attempts left' %
                (config.getint('mongodb', 'connect_wait'), config.getint('mongodb', 'connect_retry') - attempt))
            time.sleep(config.getint('mongodb', 'connect_wait'))

# Standalone run
if not args.dont_daemonize:
    output = get_config(args.resource, args.key)
    if args.json:
        print json.dumps(output, indent = 4) + '\n'
    else:
        print yaml.safe_dump(output, indent = 4, default_flow_style = False)
    sys.exit(0)

# Initiate Flask
app = flask.Flask(__name__)
auth = HTTPBasicAuth()

# SSL
context = None
if config.getboolean('http', 'use_ssl'):
    context = SSL.Context(SSL.SSLv23_METHOD)

    if not isfile(config.get('http', 'ssl_pkey')):
        error("SSL private key doesn't exist: %s" % config.get('http', 'ssl_pkey'))
    info('Load SSL private key: %s' % config.get('http', 'ssl_pkey'))
    context.use_privatekey_file(config.get('http', 'ssl_pkey'))

    if not isfile(config.get('http', 'ssl_cert')):
        error("SSL certificate doesn't exist: %s" % config.get('http', 'ssl_cert'))
    info('Load SSL certificate key: %s' % config.get('http', 'ssl_cert'))
    context.use_certificate_file(config.get('http', 'ssl_cert'))

@auth.verify_password
def verify_password(username, password):
    ld = ldap.initialize('ldaps://' + config.get('ad', 'server'))
    ld.set_option(ldap.OPT_X_TLS_DEMAND, True)

    try:
        ld.simple_bind_s(config.get('ad', 'domain') + '\\' + username, password)
        return True
    except ldap.INVALID_CREDENTIALS:
        warn('Login failed for user: %s incorrect user or password' % username)
        return False
    except ldap.LDAPError, e:
        if type(e.message) == dict and e.message.has_key('desc'):
            warn('Login failed for user: %s error: %s' % (username, e.message['desc']))
        else:
            warn('Login failed for user: %s error: %s' % (username, e))
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
    output = {}
    if config.get('main', 'backend') == 'file' or resource == 'schemas':
        files = glob(makepath(basedir, 'base', resource, 'inputs', '*'))
        for file in files:
            key = splitext(basename(file))[0]
            output[key] = get_config(resource, key)
    else:
        for entry in dbo[resource].find():
            key = entry[config.get(resource, 'key')]
            output[key] = get_config(resource, key)
    return output

@app.route('/<resource>', methods=["POST"])
if 'POST' in auth_required:
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

    if config.get('main', 'backend') == 'file':
        fn = makepath(basedir, 'base', resource, 'inputs', data[config.get(resource, 'key')])
        if isfile(fn + '.yaml') or isfile(fn + '.json'):
            data['success'] = False
            data['error'] = 'Duplicate entry, entry already exists'
            return data, 409

        f = open(fn + '.yaml', 'w')
        f.write(yaml.safe_dump(data, indent = 4, default_flow_style = False))
        f.close()
    else:
        # Check if already exists
        if not dbo[resource].find_one({ config.get(resource, 'key'): data[config.get(resource, 'key')] }):
            dbo[resource].insert(data, safe = True)
            del data['_id']
        else:
            data['success'] = False
            data['error'] = 'Duplicate entry, entry already exists'
            return data, 409

    data['success'] = True
    return data, 201

@app.route('/<resource>/<key>', methods=["PATCH"])
if 'PATCH' in auth_required:
    @auth.login_required
@mimerender(
    default = 'yaml',
    yaml  = render_yaml,
    json = render_json
)
def modify_resource(resource, key):
    data = {}

    if config.get('main', 'backend') == 'file':
        fn = makepath(basedir, 'base', resource, 'inputs', key)
        if isfile(fn + '.yaml'):
            info("Load resource input: %s" % fn)
            data = yaml.load(open(fn + '.yaml', 'r'))
        elif isfile(fn + '.json'):
            info("Load resource input: %s" % fn)
            data = json.loads(open(fn + '.json', 'r'))
    else:
        data = dbo[resource].find_one({config.get(resource, 'key'): key})
        del data['_id']

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

    if config.get('main', 'backend') == 'file':
        if isfile(fn + '.yaml'):
            f = open(fn + '.yaml', 'w')
            f.write(yaml.safe_dump(data, indent = 4, default_flow_style = False))
            f.close()
        elif isfile(fn + '.json'):
            f = open(fn + '.json', 'w')
            f.write(json.dumps(data, indent = 4))
            f.close()
    else:
        dbo.repo.update({config.get(resource, 'key'): key}, data)

    data['success'] = True
    return data, 200

@app.route('/<resource>/<key>', methods=["GET"])
if 'GET' in auth_required:
    @auth.login_required
@mimerender(
    default = 'yaml',
    yaml  = render_yaml,
    json = render_json
)
def get_resource(resource, key):
# get_config does sys.exit on missing resource, needs to raise an exception
    data = get_config(resource, key)
    return data, 200

@app.route('/<resource>/<key>', methods=["DELETE"])
if 'DELETE' in auth_required:
    @auth.login_required
@mimerender(
    default = 'yaml',
    yaml  = render_yaml,
    json = render_json
)
def delete_resource(resource, key):
    data = {}
    if config.get('main', 'backend') == 'file':
        fn = makepath(basedir, 'base', resource, 'inputs', key)
        if isfile(fn + '.json'):
            unlink(fn + '.json')
        if isfile(fn + '.yaml'):
            unlink(fn + '.yaml')
        else:
            data['success'] = false
            data['error'] = "Entry not found"
            return data, 404
    else:
        dbo[resource].remove({config.get(resource, 'key'): key})

    data['success'] = True
    return data, 204

if __name__ == '__main__':
    if config.getboolean('http', 'use_ssl'):
        info('Start with SSL support enabled')
        app.run(debug = args.debug, host = config.get('http', 'host'), port = config.getint('http', 'port'), ssl_context = context)
    else:
        app.run(debug = args.debug, host = config.get('http', 'host'), port = config.getint('http', 'port'))
