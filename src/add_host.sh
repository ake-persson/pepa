#!/bin/bash

read -d '' yaml <<__EOT__
host: dumdum.example.com
region: emea
country: nl
roles:
  - server
environment: dev
__EOT__

curl -v -X POST -H 'Content-type: application/yaml' -d "${yaml}" http://127.0.0.1:5000/hosts
