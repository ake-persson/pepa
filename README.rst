Pepa
====

Configuration templating for SaltStack using Hierarchical substitution and Jinja.

.. image:: https://drone.io/github.com/mickep76/pepa/status.png
  :alt: drone.io build status
  :target: https://drone.io/github.com/mickep76/pepa

Pepa is part of the SaltStack as of release 2014.7.

Quick testing
=============

You can easily test Pepa from the Command Line.

Create a virtual env. and install the required modules.

.. code-block:: bash

  virtualenv venv
  cd venv
  source bin/activate
  pip install pepa

Clone and run Pepa.

.. code-block:: bash

  git clone https://github.com/mickep76/pepa.git
  cd pepa
  pepa -c examples/master test.example.com -d

Install Pepa
============

.. code-block:: bash

  git clone https://github.com/mickep76/pepa.git
  mkdir -p /srv/salt/ext/pillar
  cp ext_pillar/pepa.py /srv/salt/ext/pillar/pepa.py

Configuring Pepa
================

.. code-block:: yaml

    extension_modules: /srv/salt/ext

    ext_pillar:
      - pepa:
          resource: host                # Name of resource directory and sub-key in pillars
          sequence:                     # Sequence used for hierarchical substitution
            - hostname:                 # Name of key
                name: input             # Alias used for template directory
                base_only: True         # Only use templates from Base environment, i.e. no staging
            - default:
            - environment:
            - location..region:
                name: region
            - location..country:
                name: country
            - location..datacenter:
                name: datacenter
            - roles:
            - osfinger:
                name: os
            - hostname:
                name: override
                base_only: True
          subkey: True                  # Create a sub-key in pillars, named after the resource in this case [host]
          subkey_only: True             # Only create a sub-key, and leave the top level untouched

    pepa_roots:                         # Base directory for each environment
      base: /srv/pepa/base              # Path for base environment
      dev: /srv/pepa/base               # Associate dev with base
      qa: /srv/pepa/qa
      prod: /srv/pepa/prod

    # Use a different delimiter for nested dictionaries, defaults to '..' since some keys may use '.' in the name
    #pepa_delimiter: ..

    # Supply Grains for Pepa, this should **ONLY** be used for testing or validation
    #pepa_grains:
    #  environment: dev

    # Supply Pillar for Pepa, this should **ONLY** be used for testing or validation
    #pepa_pillars:
    #  saltversion: 0.17.4

    # Enable debug for Pepa, and keep Salt on warning
    #log_level: debug

    #log_granular_levels:
    #  salt: warning
    #  salt.loaded.ext.pillar.pepa: debug

Pepa can also be used in Master-less SaltStack setup.

Command line
============

.. code-block:: bash

    usage: pepa [-h] [-c CONFIG] [-d] [-g GRAINS] [-p PILLAR] [-n] [-v]
                hostname

    positional arguments:
      hostname              Hostname

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            Configuration file
      -r RESOURCE, --resource RESOURCE
                            Resource, defaults to first resource
      -d, --debug           Print debug info
      -g GRAINS, --grains GRAINS
                            Input Grains as YAML
      -p PILLAR, --pillar PILLAR
                            Input Pillar as YAML
      -n, --no-color        No color output
      -v, --validate        Validate output

Templates
=========

Templates is configuration for a host or software, that can use information from Grains or Pillars. These can then be used for hierarchically substitution.

**Example File:** host/input/test_example_com.yaml

.. code-block:: yaml

    location..region: emea
    location..country: nl
    location..datacenter: foobar
    environment: dev
    roles:
      - salt.master
    network..gateway: 10.0.0.254
    network..interfaces..eth0..hwaddr: 00:20:26:a1:12:12
    network..interfaces..eth0..dhcp: False
    network..interfaces..eth0..ipv4: 10.0.0.3
    network..interfaces..eth0..netmask: 255.255.255.0
    network..interfaces..eth0..fqdn: {{ hostname }}
    cobbler..profile: fedora-19-x86_64

As you see in this example you can use Jinja directly inside the template.

**Example File:** host/region/amer.yaml

.. code-block:: yaml

    network..dns..servers:
      - 10.0.0.1
      - 10.0.0.2
    time..ntp..servers:
      - ntp1.amer.example.com
      - ntp2.amer.example.com
      - ntp3.amer.example.com
    time..timezone: America/Chihuahua
    yum..mirror: yum.amer.example.com

Each template is named after the value of the key using lowercase and all extended characters are replaced with underscore.

**Example:**

osfinger: Fedora-19

**Would become:**

fedora_19.yaml

Nested dictionaries
===================

In order to create nested dictionaries as output you can use double dot **".."** as a delimiter. You can change this using "pepa_delimiter" we choose double dot since single dot is already used by key names in some modules, and using ":" requires quoting in the YAML.

**Example:**

.. code-block:: yaml

    network..dns..servers:
      - 10.0.0.1
      - 10.0.0.2
    network..dns..options:
      - timeout:2
      - attempts:1
      - ndots:1
    network..dns..search:
      - example.com

**Would become:**

.. code-block:: yaml

    network:
      dns:
        servers:
          - 10.0.0.1
          - 10.0.0.2
        options:
          - timeout:2
          - attempts:1
          - ndots:1
        search:
          - example.com

Operators
=========

Operators can be used to merge/unset a list/hash or set the key as immutable, so it can't be changed.

=========== ================================================
Operator    Description
=========== ================================================
merge()     Merge list or hash
unset()     Unset key
immutable() Set the key as immutable, so it can't be changed
imerge()    Set immutable and merge
iunset()    Set immutable and unset
=========== ================================================

**Example:**

.. code-block:: yaml

    network..dns..search..merge():
      - foobar.com
      - dummy.nl
    owner..immutable(): Operations
    host..printers..unset():
