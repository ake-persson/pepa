#!/usr/bin/env python

import ConfigParser
import argparse
import json
import yaml
from os import unlink
from os.path import isfile, join as makepath, splitext, basename
import sys
from sys import stderr
from  glob import glob
import re
from termcolor import colored
import pymongo
from bson.objectid import ObjectId

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

# Get command line options
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help = 'Configuration file', default = '/etc/pepa/pepa.conf')
parser.add_argument('-d', '--debug', help = 'Print debug information', action = 'store_true', default = False)
parser.add_argument('-n', '--no-color', help = 'No color', dest = 'color', action = 'store_false', default = True)
parser.add_argument('-j', '--json', help = 'JSON output, instead of default YAML', action = 'store_true', default = False)
parser.add_argument('-r', '--resource', help = 'Resource')
args = parser.parse_args()

# Check that configuration file exist's
if not isfile(args.config):
    error("Configuration file doesn't exist: %s" % args.config)

# Get configuration
config = ConfigParser.ConfigParser()

# Set defaults
config.add_section('main')
config.set('main', 'basedir', '/srv/pepa')
config.set('main', 'environments', 'base')
config.set('main', 'resources', 'hosts')
config.add_section('mongodb')
config.set('mongodb', 'server', '127.0.0.1')
config.set('mongodb', 'port', '27017')
config.set('mongodb', 'database', 'pepa')
config.add_section('hosts')
config.set('hosts', 'key', 'hostname')

# Get config
config.read([args.config])
basedir = config.get('main', 'basedir')
resources = re.split('\s*,\s*', config.get('main', 'resources'))

# Initiate MongoDB
database = config.get('mongodb', 'database')
info('Using MongoDB backend with database: %s' % database)
conn = pymongo.Connection(config.get('mongodb', 'server'), config.getint('mongodb', 'port'))
dbo = conn[database]

files = glob(makepath(config.get('main', 'basedir'), 'base', args.resource, 'inputs', '*'))
for fn in files:
    (key, ext) = splitext(basename(fn))

    data = None
    if ext == '.yaml':
        info("Load resource: %s.yaml" % fn)
        data = yaml.load(open(fn).read())
    else:
        info("Load resource: %s.json" % fn)
        data = json.loads(open(fn).read())

    info("Import resource: %s" % key)
    dbo[args.resource].insert(data, safe = True)