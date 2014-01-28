# Pepa #

Hierarchical substitution templating for SaltStack configuration also support's the use of Jinja2.

## Build RPM ##

*Pre-requisites*

    $ sudo yum install -y pandoc rpm-build python-virtualenv gcc

*Build RPM*

Add your user to the admin group on your system and then:

    $ git clone ...
    $ cd pepa
    $ sudo chgrp admin /opt
    $ sudo chmod 770 /opt
    $ make

## Install system wide ##

    $ sudo yum install -y python-pip gcc
    $ cd pepa/
    $ sudo pip install -r ./requirements.txt
    $ cp src/pepa.py /usr/bin/pepa

## Install in a Virtual Environment ##

    $ sudo yum install -y python-virtualenv gcc
    $ virtualenv -p python2.7 ~/venv_pepa
    $ ~/venv_pepa/bin/pip install -r ./requirements.txt
    $ cp src/pepa.py ~/venv_pepa/bin/

## Example ##

    $ cd pepa/src/
    $ ./pepa.py --config ../example/conf/pepa.conf --resource hosts --key foobar.example.com -d

## Run as a Web service ##

    $ cd pepa/src/
    $ ./pepa.py --config ../example/conf/pepa.conf --daemonize

*Query REST API for all host's*

    $ curl http://127.0.0.1:5000/hosts

*Query REST API for a host*

    $ curl http://127.0.0.1:5000/hosts/foobar.example.com

# TODO #

- CLI based on the JSON Schema
- Fix Git backend once PyGit2 supports SSH and HTTPS Auth.
- Add MongoDB backend support
- Add support for group of items like host group
- REST POST support
- Authentication for Endpoints using LDAP
- Authorisation for Endpoints based on Roles
- Add REST queries for specific attributes
- Add MIME type awareness to REST API both input/output
- Add proper error checking and HTTP error codes

# License #

See the file LICENSE.
