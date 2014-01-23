#!.venv/bin/python2.7

import json
from jsonschema import validate

basedir = '/Users/mpersson/Code/pepa/example'
schemadir = basedir + '/base/schemas'

types_file = open(schemadir + '/types.json', 'r')
types_schema = json.load(types_file)

#with open(schemadir + '/input.json', 'r') as input_file:
#    input_schema = json.load(input_file)

#types_u = json.load(types_schema)
#input_u = json.load(input_schema)

#print types_u
#print input_u
