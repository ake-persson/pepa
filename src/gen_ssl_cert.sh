#!/bin/bash

BASEDIR=example/ssh

mkdir -p ${BASEDIR}
openssl genrsa -des3 -passout pass:x -out ${BASEDIR}/server.pass.key 2048
openssl rsa -passin pass:x -in ${BASEDIR}/server.pass.key -out ${BASEDIR}/server.key
rm -f ${BASEDIR}/server.pass.key
openssl req -new -key ${BASEDIR}/server.key -out ${BASEDIR}/server.csr
openssl x509 -req -days 365 -in ${BASEDIR}/server.csr -signkey ${BASEDIR}/server.key -out ${BASEDIR}/server.crt