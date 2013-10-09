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
parser.add_option('--host', help='Hostname', dest = 'host', action ='store')
(opts, args) = parser.parse_args()

# Check that configuration file exist's
if not os.path.isfile(opts.config):
    error("Configuration file doesn't exist: %s" % opts.config)

# Check options
if not opts.host:
    error("You need to specify a host")
host = opts.host

# Get configuration
config = ConfigParser.ConfigParser()
config.read([opts.config])
sequence = re.split('\s*,\s*', config.get('host', 'sequence'))
basedir = config.get('main', 'basedir')

# Load host input
file = basedir + '/input/hosts/' + host + '.sls'
if not os.path.isfile(file):
    error("Host is not defined: %s" % opts.host)
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

if opts.json:
    print json.dumps(output, indent = 4) + '\n'
else:
    print yaml.safe_dump(output, indent = 4, default_flow_style = False)
