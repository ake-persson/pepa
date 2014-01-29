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

    $ cd pepa
    $ src/pepa.py --config example/conf/pepa.conf --resource hosts --key foobar.example.com -d

## Run as a Web service ##

    $ cd pepa
    $ src/pepa.py --config example/conf/pepa.conf --daemonize

*Query REST API for all host's*

    $ curl http://127.0.0.1:8080/hosts

*Query REST API for a host*

    $ curl http://127.0.0.1:8080/hosts/foobar.example.com

*Query REST API for all user's*

    $ curl http://127.0.0.1:8080/users

*Query REST API for a user*

    $ curl http://127.0.0.1:8080/users/jdoe

# TODO #

- CLI based on the input JSON Schema
- REST POST support
- Authentication for Endpoints using LDAP
- Authorisation for Endpoints based on Roles

# License #

See the file LICENSE.
