#!/usr/bin/env python

# Environments per branch, one clone or one per branch?
# This service can easily be load balanced ;D
#

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
from flask.views import MethodView
from gittle import Gittle, GittleAuth

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
config.add_section('http')
config.set('http', 'host', '127.0.0.1')
config.set('http', 'port', 5000)

# Get config
config.read([opts.config])
sequence = re.split('\s*,\s*', config.get('host', 'sequence'))
basedir = config.get('main', 'basedir')
backend = config.get('main', 'backend')

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

    if os.path.isdir(basedir + '/.git'):
        if opts.debug:
            info("Doing a Git pull for: %s in: %s" % (uri, basedir))
        repo = Gittle(basedir, uri)
        repo.pull()
    else:
        if opts.debug:
            info("Doing a Git clone for: %s to: %s" % (uri, basedir))
        repo = Gittle.clone(uri, basedir)

    if config.has_option('git', 'subdir'):
        basedir += '/' + config.get('git', 'subdir')

def get_config(host):

    # Load host input
    file = basedir + '/inputs/hosts/' + host + '.sls'
    if not os.path.isfile(file):
        error("Host is not defined: %s" % host)
    input = yaml.load(open(file, 'r').read())
    input['default'] = 'default'

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
            file = basedir + '/templates/' + category + '/' +  re.sub('\W', '_', entry.lower()) + '.sls'
            if os.path.isfile(file):
                if opts.debug:
                    info("Parsing template: %s" % file)
                template = Template(open(file).read())
                config = yaml.load(template.render(output))
                for key in config:
                    if opts.debug:
                        info2("Substituting key: %s" % key)
                    output[key] = config[key]
            else:
                if opts.debug:
                    warn("Template doesn't exist: %s" % file)
    return output

class Host(MethodView):
    def get(self):
        files = glob.glob(basedir + '/inputs/hosts/*.sls')
        hosts = []
        for file in files:
            hosts.append(splitext(basename(file))[0])
        return yaml.safe_dump(hosts, indent = 4, default_flow_style = False)

app.add_url_rule('/hosts/', view_func = Host.as_view('hosts'))

class HostObject(MethodView):
    def get(self, host):
        output = get_config(host)
        return yaml.safe_dump(output, indent = 4, default_flow_style = False)

app.add_url_rule('/hosts/<host>', view_func = HostObject.as_view('host_object'))

# Add REST call for triggering Git pull
#app.add_url_rule('/git/<pull>', view_func = HostObject.as_view('git'))

if __name__ == '__main__' and opts.daemonize:
    app.run(debug = True, host = config.get('http', 'host'), port = config.get('http', 'port'))
else:
    output = get_config(opts.host)
    if opts.json:
        print json.dumps(output, indent = 4) + '\n'
    else:
        print yaml.safe_dump(output, indent = 4, default_flow_style = False)
