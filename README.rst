Configuration templating using Hierarchical substitution and Jinja.

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

# Enable debug for Pepa, and keep Salt on warning
#log_level: debug

#log_granular_levels:
#  salt: warning
#  salt.loaded.ext.pillar.pepa: debug

.. code-block:: yaml

Pepa can also be used in Master-less SaltStack setup.

Command line
============

.. code-block:: bash

usage: pepa.py [-h] [-c CONFIG] [-d] [-g GRAINS] [-p PILLAR] [-n] [-v]
               hostname

positional arguments:
  hostname              Hostname

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file
  -d, --debug           Print debug info
  -g GRAINS, --grains GRAINS
                        Input Grains as YAML
  -p PILLAR, --pillar PILLAR
                        Input Pillar as YAML
  -n, --no-color        No color output
  -v, --validate        Validate output

.. code-block:: bash

Templates
=========

Templates is configuration for a host or software, that can use information from Grains or Pillars. These can then be used for hierarchically substitution.

**Example File:** host/input/test.example.com.yaml

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

.. code-block:: yaml

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

.. code-block:: yaml

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

.. code-block:: yaml

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

.. code-block:: yaml

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

.. code-block:: yaml

Validation
==========

Since it's very hard to test Jinja as is, the best approach is to run all the permutations of input and validate the output, i.e. Unit Testing.

To facilitate this in Pepa we use YAML, Jinja and Cerberus <https://github.com/nicolaiarocci/cerberus>.

Schema
======

So this is a validation schema for network configuration, as you see it can be customized with Jinja just as Pepa templates.

This can be run in master-less setup or without SaltStack. If you run it without SaltStack you can provide Grains/Pillar input using either the config file or command line arguments.

**File Example: host/validation/network.yaml**

.. code-block:: yaml

network..dns..search:
  type: list
  allowed:
    - example.com

# Should be list of hash values
network..dns..options:
  type: list
  allowed: ['timeout:2', 'attempts:1', 'ndots:1']

network..dns..servers:
  type: list
  schema:
    regex: ^([0-9]{1,3}\.){3}[0-9]{1,3}$

network..gateway:
  type: string
  regex: ^([0-9]{1,3}\.){3}[0-9]{1,3}$

{% if network.interfaces is defined %}
{% for interface in network.interfaces %}

network..interfaces..{{ interface }}..dhcp:
  type: boolean

network..interfaces..{{ interface }}..fqdn:
  type: string
  regex: ^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-zA-Z]{2,6}$

network..interfaces..{{ interface }}..hwaddr:
  type: string
  regex: ^([0-9a-f]{1,2}\:){5}[0-9a-f]{1,2}$

network..interfaces..{{ interface }}..ipv4:
  type: string
  regex: ^([0-9]{1,3}\.){3}[0-9]{1,3}$

network..interfaces..{{ interface }}..netmask:
  type: string
  regex: ^([0-9]{1,3}\.){3}[0-9]{1,3}$

{% endfor %}
{% endif %}

.. code-block:: yaml
