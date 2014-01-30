#!.venv/bin/python2.7

import json
import yaml
import argparse
from prettytable import PrettyTable
import requests
import ConfigParser
from os.path import exists, expanduser
from termcolor import colored
import sys
from sys import stderr
from requests.auth import HTTPBasicAuth
import getpass

def info(message):
    print >> stderr, colored(message, 'green')

def warn(message):
    print >> stderr, colored(message, 'yellow')

def error(message, code):
    print >> stderr, colored(message, 'red')
    sys.exit(code)

url = 'http://127.0.0.1:8080'
headers = {'content-type': 'application/json', 'accept': 'application/json'}
actions = [ 'get', 'add', 'modify', 'delete', 'list' ]

request = requests.get(url + '/schemas', headers = headers)

if request.status_code == 401:
    if username == None: username = getpass.getuser()
    if password == None: password = getpass.getpass()
    request = requests.get(url + '/schemas', headers = headers, auth = (username, password))

if request.status_code != 200:
    error(request.text, request.status_code)

schemas = request.json()
resources = schemas.keys()

parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(dest = 'action')
parser.add_argument('-c', '--config', default = '/etc/pepa.conf', help = 'Configuration file')
parser.add_argument('-d', '--debug', action = 'store_true', help = 'Print debug info')

parsers = {}
for action in actions:
    parsers[action, 'first'] = subparser.add_parser(action)
    parsers[action, 'second'] = parsers[action, 'first'].add_subparsers(dest = 'resource')
    for resource in resources:
        parsers[action, resource] = parsers[action, 'second'].add_parser(resource)
        key = schemas[resource]['id']
        parsers[action, resource].add_argument(key, help = key)

args = parser.parse_args()