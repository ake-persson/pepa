#!.venv/bin/python2.7

import json
from jsonschema import validate

def expand_schema(types, schema):
    if isinstance(schema, dict):
        for entry in schema:
            if isinstance(schema[entry], dict) and 'type' in schema[entry]:
                if schema[entry]['type'] in types:
                    schema[entry].update(types[schema[entry]['type']])
            expand_schema(types, schema[entry])

basedir = '/Users/mpersson/Code/pepa/example'
schemadir = basedir + '/base/schemas'

types_file = open(schemadir + '/types.json', 'r')
types_schema = json.load(types_file)

input_file = open(schemadir + '/input.json', 'r')
input_schema = json.load(input_file)

expand_schema(types_schema, input_schema)
print json.dumps(input_schema, indent = 4)
