# Pepa #

Hierarchical substitution templating for SaltStack configuration also support's the use of Jinja2.

## Build RPM ##

*Pre-requisites*

    $ sudo yum install -y pandoc rpm-build python-virtualenv gcc openldap-devel openssl-devel

*Build RPM*

Add your user to the wheel group on your system:

    $ sudo groupmems -a &lt;username&gt; -g wheel
    $ newgrp wheel
    $ sudo chgrp wheel /opt
    $ sudo chmod 775 /opt

Now you can build the RPM:

    $ git clone ...
    $ cd pepa
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

*Query REST API for a host, and return it as JSON*

    $ curl -H "Accept: application/json" http://127.0.0.1:8080/hosts/foobar.example.com

*Query REST API for all user's, and return it as YAML*

    $ curl -H "Accept: application/yaml" http://127.0.0.1:8080/users

*Query REST API for a user*

    $ curl -H "Accept: application/json" http://127.0.0.1:8080/users/jdoe

# DOCUMENTATION #

More documentation can be found in the doc/ folder.

# TODO #

- 2 Security groups in AD for roles for Pepa. This means it can be managed by IAM with the AD driver.
  + Unprivileged
    - Can query all entries
  + Normal user
    - Can create new entries
    - Can modify existing entries they created
    - Can delete existing entries they created
  + Admin
    - Full access
- Use JavaScript framework to template GUI based on JSON schema
- Puppet option in config
- Default datatype in API YAML or JSON, should be configurable
- Query language to ask for specific attributes
- Version API
- Git hooks for validating input
- Modify templates using REST API
- Error messages def. to support JSON error
- Modify/rename hostname/username i.e. using the key in CLI
- Validate Input/Output Git hooks

# License #

See the file LICENSE.
