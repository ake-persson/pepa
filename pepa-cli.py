#!/usr/bin/env python -u
# -*- coding: utf-8 -*-

import argparse
import sys
from os.path import isfile
import yaml
import logging
import pepa

# Create formatter
try:
    import colorlog
    formatter = colorlog.ColoredFormatter("[%(log_color)s%(levelname)-8s%(reset)s] %(log_color)s%(message)s%(reset)s")
except ImportError:
    formatter = logger.Formatter("[%(levelname)-8s] %(message)s")

# Create console handle
console = logging.StreamHandler()
console.setFormatter(formatter)

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console)

# Create logger for module
logger_pepa = logging.getLogger('pepa')
logger_pepa.setLevel(logging.DEBUG)
logger_pepa.addHandler(console)

# Get arguments
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='Hostname')
parser.add_argument('-c', '--config', default='/etc/salt/master', help='Configuration file')
parser.add_argument('-d', '--debug', action='store_true', help='Print debug info')
parser.add_argument('-g', '--grains', help='Input Grains as YAML')
parser.add_argument('-p', '--pillar', help='Input Pillar as YAML')
parser.add_argument('-n', '--no-color', action='store_true', help='No color output')
args = parser.parse_args()

# Load configuration file
if not isfile(args.config):
    logger.critical("Configuration file doesn't exist: {0}".format(args.config))
    sys.exit(1)

# Get configuration
conf = yaml.load(open(args.config).read())
loc = 0
for name in [e.keys()[0] for e in conf['ext_pillar']]:
    if name == 'pepa':
        break
    loc += 1

# Get grains
grains = {}
if 'pepa_grains' in conf:
    grains = conf['pepa_grains']
if args.grains:
    grains.update(yaml.load(args.grains))

# Get pillar
pillar = {}
if 'pepa_pillar' in conf:
    pillar = conf['pepa_pillar']
if args.pillar:
    pillar.update(yaml.load(args.pillar))

p = conf['ext_pillar'][loc]['pepa']
templ = pepa.Template(roots=conf['pepa_roots'], resource=p['resource'], sequence=p['sequence'])
res = templ.compile(minion_id='test.example.com', grains=grains, pillar=pillar)

yaml.dumper.SafeDumper.ignore_aliases = lambda self, data: True
print yaml.safe_dump(res)
