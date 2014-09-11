Configuration templating using Hierarchical substitution and Jinja.

Configuring Pepa
================

.. code-block:: yaml

extension_modules: /srv/salt/ext

.. code-block:: yaml

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

.. code-block:: yaml

pepa_roots:                         # Base directory for each environment
  base: /srv/pepa/base              # Path for base environment
  dev: /srv/pepa/base               # Associate dev with base
  qa: /srv/pepa/qa
  prod: /srv/pepa/prod

.. code-block:: yaml

# Use a different delimiter for nested dictionaries, defaults to '..' since some keys may use '.' in the name
#pepa_delimiter: ..

.. code-block:: yaml

# Enable debug for Pepa, and keep Salt on warning
#log_level: debug

.. code-block:: yaml

#log_granular_levels:
#  salt: warning
#  salt.loaded.ext.pillar.pepa: debug

Pepa can also be used in Master-less SaltStack setup.
