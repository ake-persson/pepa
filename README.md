# Installation

- Create folder */srv/salt/ext/pillar*
- Copy file *pepa.py* to */srv/salt/ext/pillar*
- Modify */etc/salt/master* and add the following

```yaml
extension_modules : /srv/salt/ext

ext_pillar:
  - pepa:
      resource: hosts
      grains:
        - osfinger
      sequence:
        - default
        - environment
        - region
        - country
        - roles
        - osfinger
        - hostname

pepa_roots:
  dev: /srv/salt/base
  qa: /srv/salt/qa
  prod: /srv/salt/prod
```

# Configuration

```yaml
ext_pillar:
  - pepa:
      resource: hosts             # Name of resource directory
      grains:                     # List of grain's to import
        - osfinger
      sequence:                   # Sequence of hierarchical substitution
        - default
        - environment
        ...

pepa_roots:                     # Base directory for each environment
  dev: /srv/salt/base
  ...
```

# Input

Input is basically authoritative information for a host, you don't necessarily need this since you can use Grains or other Ext. Pillars for this.

**Ex.**

**File:** /srv/salt/base/hosts/inputs/rocksalt.example.com.yaml

```yaml
hostname: rocksalt.example.com
region: emea
country: nl
environment: dev
host_type: server
roles:
  salt-master
```

# Templates

Templates are located based on the *pepa_roots*. So for the above configuration templates for *Dev* would be located as follows:

```yaml
/srv/salt/dev/hosts/templates
    default
    environment
    region
    ...
```

Each template is named the value of the key using lowercase and all extended characters are replaces with underscore.

**Ex.:**

    osfinger: Fedora-19

**Would become:**

    fedora_19.yaml

# Nested dictionaries

In order to create nested dictionaries as output you can use dot **(.)** as a separator.

**Ex.**

```yaml
dns.servers:
  - 10.0.0.1
  - 10.0.0.2
dns.options:
  - timeout:2
  - attempts:1
  - ndots:1
dns.search:
  - example.com
```

**Would become:**

```yaml
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

# Validation
