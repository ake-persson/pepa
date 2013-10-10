# Pepa #

Hierarchical substitution templating for SaltStack configuration also support's the use of Jinja2.

## Build RPM ##

*Pre-requisites*

    $ sudo yum install -y pandoc rpm-build python-virtualenv

*Build RPM*

    $ git clone ...
    $ cd pepa
    $ ./build_venv.sh
    $ make

## Example ##

    $ cd pepa/src
    $ ./pepa.py --config ../example/conf/pepa.conf --host foobar.example.com -d

## Run as a REST API ##

    $ cd pepa/src
    $ ./pepa.py --config ../example/conf/pepa.conf --daemonize

*Query REST API for all host's*

    $ curl http://127.0.0.1:5000/hosts

*Query REST API for a host*

    $ curl http://127.0.0.1:5000/hosts/foobar.example.com

# TODO #

- Add MIME type awareness to REST API both input/output
- Add some regexp validation for input
- Add support for talking to Git directly as a back-end
- Add support for importing Grains when running as a Pillar plugin
- Add a separate validation tool for input and output using YAML/JSON schema

# License #

See the file LICENSE.
