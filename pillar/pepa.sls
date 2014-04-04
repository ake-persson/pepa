#!py

import logging
import salt
import salt.log
import salt.modules.network
import salt.modules.cmdmod

log = logging.getLogger(__name__)
log.warn("Availabe stuff: {0}".format(dir())) #"

import requests
import yaml

def run():
  # This is the trick to accessing grains from within pillar python code
  log.warn("Mygrains: {0}".format(grains))

  fqdn = grains['fqdn']
  pepa_server = 'pepa'
  pepa_ssl = True
  pepa_protocol = 'https'

  data = {}

  if 'pepa_server' in grains:
    pepa_server = grains['pepa_server']

  if 'pepa_port' in grains:
    pepa_port = grains['pepa_port']|string()

  if 'pepa_ssl' in grains:
    pepa_ssl = grains['pepa_ssl']

  if pepa_ssl == False:
    pepa_protocol = 'http'

  pepa_url = '%s://%s:%s/hosts/%s' % (pepa_protocol, pepa_server, pepa_port, fqdn)

  try:
    request = requests.get(data['pepa_url'], verify = False)
    data = yaml.load(request.text)
  except:
    pass

  if data:
    return data
