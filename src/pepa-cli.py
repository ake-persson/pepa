#!/opt/pepa/bin/python2

import json
import yaml
import argparse
from prettytable import PrettyTable
import requests
import ConfigParser
from os.path import exists, expanduser, isfile
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

def error(message, code = 1):
    print >> stderr, colored(message, 'red')
    sys.exit(code)

def unique(a):
    return OrderedDict.fromkeys(a).keys()

# Get configuration
config = ConfigParser.ConfigParser()

# Set defaults
config.add_section('client')
config.set('client', 'url', 'http://127.0.0.1:8080')
config.set('client', 'verify_ssl', False)
config.set('client', 'username', None)
config.set('client', 'password', None)

# Get config
cfile = None
if isfile('/etc/pepa/pepa.conf'):
    cfile = '/etc/pepa/pepa.conf'
if isfile('~/.pepa.conf'):
    cfile = '~/.pepa.conf'
if cfile:
    config.read(cfile)

url = config.get('client', 'url')
headers = {'content-type': 'application/json', 'accept': 'application/json'}
actions = [ 'get', 'add', 'modify', 'delete', 'list' ]
username = config.get('client', 'username')
password = config.get('client', 'password')
verify_ssl = config.getboolean('client', 'verify_ssl')

request = requests.get(url + '/schemas', headers = headers, verify = verify_ssl)

if request.status_code != 200:
    error(request.text, request.status_code)

schemas = request.json()
resources = schemas.keys()

parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(dest = 'action')
parser.add_argument('-d', '--debug', action = 'store_true', help = 'Print debug info')

parsers = {}
for action in actions:
    parsers[action, 'first'] = subparser.add_parser(action)
    parsers[action, 'second'] = parsers[action, 'first'].add_subparsers(dest = 'resource')
    for resource in resources:
        parsers[action, resource] = parsers[action, 'second'].add_parser(resource)

        if not 'id' in schemas[resource]:
            error("Schema: %s needs to declare an id" % resource)
        key = schemas[resource]['id']

        required_fields = [ key ]
        if 'required' in schemas[resource]:
            required_fields = schemas[resource]['required']

        if action == 'list':
            parsers[action, resource].add_argument('--format', choices = ['text', 'table', 'csv', 'json', 'yaml'], default = 'text', help = 'Print format')
            parsers[action, resource].add_argument('--fields', help = 'Fields to print, ignored by JSON or YAML')
# Add sort by
        elif action == 'get':
            descr = key.title()
            if 'properties' in schemas[resource] and 'description' in schemas[resource]['properties'][key]:
                descr = schemas[resource]['properties'][key]['description']

            parsers[action, resource].add_argument(key, help = descr)

            parsers[action, resource].add_argument('--format', choices = ['text', 'table', 'csv', 'json', 'yaml'], default = 'text', help = 'Print format')
            parsers[action, resource].add_argument('--fields', help = 'Fields to print, ignored by JSON or YAML')
        elif action == 'delete':
            descr = key.title()
            if 'properties' in schemas[resource] and 'description' in schemas[resource]['properties'][key]:
                descr = schemas[resource]['properties'][key]['description']

            parsers[action, resource].add_argument(key, help = descr)
        else:
            if 'properties' not in schemas[resource]:
                continue

            for entry in schemas[resource]['properties'].keys():
                ftype = None
                if not 'type' in schemas[resource]['properties'][entry]:
                    error("Schema: %s entry: %s needs to declare a type" % (resource, entry))
                ftype = schemas[resource]['properties'][entry]['type']

                if ftype != 'array' and ftype != 'string':
                    error("Schema: %s entry: %s has an unsupported type: %s for this CLI" % (resource, entry, ftype))

                descr = entry.title()
                if 'description' in schemas[resource]['properties'][entry]:
                    descr = schemas[resource]['properties'][entry]['description']

                if entry == key:
                    parsers[action, resource].add_argument(key, help = descr)
                    continue

                arguments = [ '--%s' % entry ]
                if 'arguments' in schemas[resource]['properties'][entry]:
                    arguments = schemas[resource]['properties'][entry]['arguments']

                choices = None
                if action != 'modify' and 'enum' in schemas[resource]['properties'][entry]:
                    choices = schemas[resource]['properties'][entry]['enum']

                required = False
                if action != 'modify' and entry in required_fields:
                    required = True

                default = None
                if action != 'modify' and 'default' in schemas[resource]['properties'][entry]:
                    default = schemas[resource]['properties'][entry]['default']

                if len(arguments) > 1:
                    parsers[action, resource].add_argument(arguments[0], arguments[1], choices = choices, required = required, default = default, help = descr)
                else:
                    parsers[action, resource].add_argument(arguments[0], choices = choices, required = required, default = default, help = descr)

# Support type array, with enum and default
# Only support array with type string entries

args = parser.parse_args()
arglist = vars(args)

if args.action == 'list' or args.action == 'get':
    key = schemas[args.resource]['id']

    request = None
    if args.action == 'get':
        request = requests.get(url + '/' + args.resource + '/' + arglist[key], headers = headers,
            verify = verify_ssl)
    else:
        request = requests.get(url + '/' + args.resource, headers = headers, verify = verify_ssl)

    if request.status_code != 200:
        error(request.text, request.status_code)

    response = None
    if args.action == 'get':
        response = { arglist[key]: request.json() }
    else:
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
        fmt_fields = re.split('\s*,\s*', args.fields)
        for field in fmt_fields:
            if field not in fields:
                error("Unknown field: %s" % field)
        fields = fmt_fields

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

if args.action == 'add':
    data = {}
    key = schemas[args.resource]['id']

    request = None
    if args.action == 'get':
        request = requests.get(url + '/' + args.resource + '/' + arglist[key], headers = headers, verify = verify_ssl)
    else:
        request = requests.get(url + '/' + args.resource, headers = headers, verify = verify_ssl)

    if request.status_code == 401:
        if username == None: username = getpass.getuser()
        if password == None: password = getpass.getpass()
        request = requests.get(url + '/' + args.resource, headers = headers, auth = (username, password), verify = verify_ssl)

    if request.status_code != 200:
        error(request.text, request.status_code)

    response = None
    if args.action == 'get':
        response = { arglist[key]: request.json() }
    else:
        response = request.json()

    required_fields = [ key ]
    if 'required' in schemas[resource]:
        required_fields = schemas[resource]['required']

    for entry in schemas[args.resource]['properties'].keys():
        ftype = schemas[args.resource]['properties'][entry]['type']
        if ftype == 'string':
            data[entry] = arglist[entry]
        else:
            data[entry] = re.split('\s*,\s*', arglist[entry])

    if username == None: username = getpass.getuser()
    if password == None: password = getpass.getpass()
    request = requests.post(url + '/' + args.resource,  json.dumps(data), headers = headers,
        auth = (username, password), verify = verify_ssl)

    if request.status_code != 201:
        error(request.text, request.status_code)
    print request.text

if args.action == 'modify':
# Change key like hostname
    key = schemas[args.resource]['id']

    data = {}
    for entry in arglist:
        if arglist[entry] and entry in schemas[args.resource]['properties'].keys():
            ftype = schemas[args.resource]['properties'][entry]['type']
            if ftype == 'string':
                data[entry] = arglist[entry]
            else:
                data[entry] = re.split('\s*,\s*', arglist[entry])

    if username == None: username = getpass.getuser()
    if password == None: password = getpass.getpass()
    request = requests.patch(url + '/' + args.resource + '/' + arglist[key],  json.dumps(data), headers = headers,
        auth = (username, password), verify = verify_ssl)

    if request.status_code != 200:
        error(request.text, request.status_code)
    print request.text

if args.action == 'delete':
    key = schemas[args.resource]['id']

    if username == None: username = getpass.getuser()
    if password == None: password = getpass.getpass()
    request = requests.delete(url + '/' + args.resource + '/' + arglist[key], headers = headers,
        auth = (username, password), verify = verify_ssl)

    # Failed
    if request.status_code != 204:
        error(request.text, request.status_code)
    print request.text
