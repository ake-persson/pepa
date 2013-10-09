# Pepa #

Hierarchical substitution templating for SaltStack configuration also support's the use of Jinja2.

## Build RPM ##

*Pre-requisites*

    $ sudo yum install -y pandoc rpm-build python-virtualenv

*Build RPM*

    $ git clone ...
    $ cd pepa
    $ ./build_venv.sh

Logout and login again to get the new group permissions.

    $ cd pepa
    $ make

## Example ##

    $ cd pepa/src
    $ ./pepa.py -c ../example/conf/pepa.conf --host foobar.example.com -d

# Roadmap #

- Add support for running it as a Web service using Flask-restless
- Add support for talking to Git directly as a back-end
- Add a separate validation tool for input and output using YAML/JSON schema

# License #

See the file LICENSE.
