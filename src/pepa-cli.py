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
from collections import OrderedDict
import re

def info(message):
    print >> stderr, colored(message, 'green')

def warn(message):
    print >> stderr, colored(message, 'yellow')

def error(message, code):
    print >> stderr, colored(message, 'red')
    sys.exit(code)

def unique(a):
    return OrderedDict.fromkeys(a).keys()

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
        if action == 'list':
            parsers[action, resource].add_argument('--format', choices = ['text', 'table', 'csv', 'json', 'yaml'], default = 'text', help = 'Print format')
            parsers[action, resource].add_argument('--fields', help = 'Fields to print, ignored by JSON or YAML')
        else:
            parsers[action, resource].add_argument(key, help = key)

args = parser.parse_args()

if args.action == 'list':

    request = requests.get(url + '/' + args.resource, headers = headers)

    if request.status_code == 401:
        if username == None: username = getpass.getuser()
        if password == None: password = getpass.getpass()
        request = requests.get(url + '/' + args.resource, headers = headers, auth = (username, password))

    if request.status_code != 200:
        error(request.text, request.status_code)
    response = request.json()

    if args.format == 'json':
        print json.dumps(response, indent = 4) + '\n'
        sys.exit(0)

    elif args.format == 'yaml':
        print yaml.safe_dump(response, indent = 4, default_flow_style = False)
        sys.exit(0)

    # Get fields in response
    fields = []
    for row in response.keys():
        fields += response[row].keys()
    fields = unique(fields)

    # Compile results
    results = {}
    for row in response.keys():
        results[row] = {}
        for field in fields:
            if field in response[row].keys():
                if isinstance(response[row][field], unicode):
                    results[row][field] = response[row][field]
                elif isinstance(response[row][field], list):
                    results[row][field] = ', '.join(response[row][field])
                else:
                    results[row][field] = str(type(response[row][field]))
            else:
                results[row][field] = 'null'

    if args.fields:
        fields = re.split('\s*,\s*', args.fields)

    if args.format == 'text':
        for row in results.keys():
            print row
            for field in fields:
                print field + ': ' + results[row][field]
            print ''

    elif args.format == 'table':
        table = PrettyTable(fields)
        for row in results.keys():
            values = []
            for field in fields:
                values.append(results[row][field])
            table.add_row(values)
        print table

    elif args.format == 'csv':
        print ','.join(['"%s"' % w for w in fields])
        for row in results.keys():
            values = []
            for field in fields:
                values.append(results[row][field])
            print ','.join(['"%s"' % w for w in values])