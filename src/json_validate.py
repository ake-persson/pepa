#!.venv/bin/python2.7

from flask import Flask, request, url_for
from flask.views import MethodView

import json
from jsonschema import validate

def expand_schema(types, schema):
    if isinstance(schema, dict):
        for entry in schema:
            if isinstance(schema[entry], dict) and 'type' in schema[entry]:
                if schema[entry]['type'] in types:
                    schema[entry].update(types[schema[entry]['type']])
            expand_schema(types, schema[entry])

api_version = 0.1
api_prefix = '/api/%s' % api_version
basedir = '/Users/mpersson/Code/pepa/example'
schemadir = basedir + '/base/schemas'

app = Flask(__name__)

types_file = open(schemadir + '/types.json', 'r')
types_schema = json.load(types_file)

input_file = open(schemadir + '/input.json', 'r')
input_schema = json.load(input_file)

expand_schema(types_schema, input_schema)
#print json.dumps(input_schema, indent = 4)

app = Flask(__name__)

class HostAPI(MethodView):
    def post(self):
        data = json.loads(request.data)
        validate(data, input_schema['user'])
# Store data in Git
        return json.dumps(data, sort_keys = True, indent = 4), 201

    def get(self):
        data = {}
# Get data from Git
        return json.dumps(data, sort_keys = True, indent = 4), 200

app.add_url_rule("%s/hosts" % api_prefix, view_func = HostAPI.as_view('host'))

if __name__ == '__main__':
    app.run(debug = True)
