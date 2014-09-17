# Pepa Roadmap

## Configuration
  
  - top.sls file
  - Option for getting Grains using REST API

Instead of using Salt master config. file, I will implement a top.sls file for consistency with Salt and allow for staging.

## Resource Inputs

  - Only key/values
  - No Jinja support
  - Backends for inputs such as ims and etcd
  - Resource tagging

Since Pillar values are not available from the REST API, we can't easily validate templates or resource configuration when we use data from IMS.

Implementing a plugin arch. allow us to properly validate templates. It also allows us to get the complete configuration
on the Command Line, this will make debbuging easier.

This also allows us to expose resources using a REST API for Pepa going forward.

## Templates

  - Add PyGit2 backend
  - Include Salt Jinja filters
  - Use function to get values, works around issue with undefined values in Jinja
  - Investigate if operators like merge(), immutable() and unset() could be Jinja filters or defines instead
  - Option to Show rendered templates 

## Validation

  - Validate templates
  - Validate resource output

Validate templates will only validate YAML/Jinja syntax, requires that undefined variables use a Jinja define.
Validate resource output will validate the output using Cerberus similar to JSON Schema.
