#!py

import logging
import salt
import salt.log

log = logging.getLogger(__name__)
log.warn("Availabe stuff: {0}".format(dir())) #"

import requests
import yaml

def run():
  # This is the trick to accessing grains from within pillar python code
  log.warn("Mygrains: {0}".format(grains))

  # Get hostname
  fqdn = grains['fqdn']

  # Pepa defaults
  data = {}
  data['pepa_server'] = 'pepa'
  data['pepa_port'] = '8080'
  data['pepa_ssl'] = True
  data['pepa_protocol'] = 'https'

  # Check if defaults we're overriden by a Grain
  if 'pepa_server' in grains:
    data['pepa_server'] = grains['pepa_server']

  if 'pepa_port' in grains:
    data['pepa_port'] = grains['pepa_port']|string()

  if 'pepa_ssl' in grains:
    data['pepa_ssl'] = grains['pepa_ssl']

  if data['pepa_ssl'] == False:
    data['pepa_protocol'] = 'http'

  # Get request url
  data['pepa_url'] = '%s://%s:%s/hosts/%s' % (data['pepa_protocol'], data['pepa_server'], data['pepa_port'], fqdn)

  # Request data
  try:
    request = requests.get(data['pepa_url'], verify = False)
    data.update(yaml.load(request.text))
  except:
    pass

  # Return data
  if data:
    return data
