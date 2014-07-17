# Quick testing

You can easily test Pepa from the Command Line.

Create a virtual env. and install the required modules.

```bash
virtualenv venv
cd venv
source bin/activate
pip install pyyaml jinja2 argparse logging colorlog
```

Clone and run Pepa.

```bash
git clone https://github.com/mickep76/pepa.git
cd pepa
./pepa.py -c examples/pepa test.example.com -d
```

You can also specify the Grains/Pillar as arguments.

```bash
./pepa.py -c examples/pepa test.example.com -g '{ osfinger: Fedora 17, os: Fedora, osrelease: 17 }'
```

Normally Grains/Pillars are supplied from the Salt master/minion, this is mostly for testing and validation.

# Installation

- Create folder */srv/salt/ext/pillar*
- Copy file *pepa.py* to */srv/salt/ext/pillar*
- Modify */etc/salt/master* and add the following

```yaml
extension_modules: /srv/salt/ext

ext_pillar:
  - pepa:
      resource: hosts
      sequence:
        - hostname:
            name: host_input
            base_only: True
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
        - hostname:
            base_only: True  

pepa_roots:
  base: /srv/salt/base
  dev: /srv/salt/base
  qa: /srv/salt/qa
  prod: /srv/salt/prod
```

# Configuration

```yaml
ext_pillar:
  - pepa:
      resource: hosts             # Name of resource directory
      sequence:                   # Sequence used for hierarchical substitution
        - hostname:               # Name of key
            name: host_input      # Alias used for template directory
            base_only: True       # Only use templates in Base environment, i.e. no staging
        - default:
        ...

pepa_roots:                       # Base directory for each environment
  dev: /srv/salt/base

pepa_subkey: True                 # Present values in subkey 'pepa: ...'
pepa_subkey_only: False           # Only present values in subkey 'pepa: ...'
```

Using pepa subkey has some advantages since you can easily see what was actually provided by Pepa using:

```bash
salt-call pillar.get pepa
```

# Templates

Templates are configuration for a host, that can use information from Grains or Pillars, these are then hierarchically substituted.

**Example:**

**File:** /srv/salt/base/hosts/host_input/test.example.com.yaml

```yaml
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
```

**File:** /srv/salt/base/hosts/region/amer.yaml

```yaml
network..dns..servers:
  - 10.0.0.1
  - 10.0.0.2
time..ntp..servers:
  - ntp1.amer.example.com
  - ntp2.amer.example.com
  - ntp3.amer.example.com
time..timezone: America/Chihuahua
yum..mirror: yum.amer.example.com
```

Each template is named the value of the key using lowercase and all extended characters are replaces with underscore.

**Example:**

    osfinger: Fedora-19

**Would become:**

    fedora_19.yaml

# Nested dictionaries

In order to create nested dictionaries as output you can use double dot **".."** as a delimiter. You can change this using "pepa_delimiter" but I choose this because single dot is already used by quite a few modules (God know's why?), and using ":" requires quoting in the YAML which is plain ugly.

**Example:**

```yaml
network.dns.servers:
  - 10.0.0.1
  - 10.0.0.2
network.dns.options:
  - timeout:2
  - attempts:1
  - ndots:1
network.dns.search:
  - example.com
```

**Would become:**

```yaml
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
```

# Logging

If you want to use different level's of logging for Salt master and Pepa, you can do this in the salt master file.

**File:** /etc/salt/master

```yaml
log_level: debug

log_granular_levels:
  salt: warning
  salt.loaded.ext.pillar.pepa: debug
```

In order for this to work log_level needs lowest level and then you can override this, it's slightly non-intuitive.
