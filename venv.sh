#!/bin/bash

VENV=.venv

virtualenv -p python2.7 ${VENV}
. ${VENV}/bin/activate
${VENV}/bin/pip install -r requirements.txt
( cd ${VENV} && rm -f lib64 && ln -s lib lib64 )
