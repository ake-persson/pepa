# Pepa #

Hierarchical substitution templating for SaltStack configuration also support's the use of Jinja2.

## Build RPM ##

*Pre-requisites*

    $ sudo yum install -y pandoc rpm-build python-virtualenv gcc

*Build RPM*

    $ git clone ...
    $ cd pepa
    $ ./build_venv.sh
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
    $ ./pepa.py --config ../example/conf/pepa.conf --host foobar.example.com -d

## Run as a Web service ##

    $ cd pepa/src/
    $ ./pepa.py --config ../example/conf/pepa.conf --daemonize

*Query REST API for all host's*

    $ curl http://127.0.0.1:5000/hosts

*Query REST API for a host*

    $ curl http://127.0.0.1:5000/hosts/foobar.example.com

## Use Git backend ##

    $ cd pepa/src
    $ ./pepa.py --config ../example/conf/pepa_git.conf --host foobar.example.com

# TODO #

- JSON Schema validation
- API based on the JSON Schema
- CLI based on the JSON Schema
- Custom substitution sequence per endpoint i.e. you can handle any input ex. input/users, input/apps
- Fix Git backend, switch out Gittle for PyGit2
- Add MongoDB backend support
- Add support for group of items like host group
- Authentication for Endpoints using LDAP
- Add REST call for triggering Git pull
- Add REST queries for specific attributes like MAC address
- Git pull must be locking so any concurrent process need to wait for completion, use a lockfile
- Add an interval for normal git pull
- Add MIME type awareness to REST API both input/output
- Add proper error checking and HTTP error codes
- Add logfile and/ or support for Syslog

# License #

See the file LICENSE.
