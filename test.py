#!/usr/bin/env python -u
# -*- coding: utf-8 -*-

import pepa

sequence = [
    { 'hostname': { 'name': 'host_input', 'base_only': True } },
    { 'default': {} },
    { 'environment': {} },
    { 'location..region': { 'name': 'region' } },
    { 'location..country': { 'name': 'country' } },
    { 'location..datacenter': { 'name': 'datacenter' } },
    { 'roles': {} },
    { 'osfinger': {} },
    { 'hostname': { 'name': 'host_override', 'base_only': True } }
]

roots = {
  'base': 'examples'
}

grains = {
  'osfinger': 'Fedora 19'
}

templ = pepa.Template(resource='hosts', roots=roots, sequence=sequence)
print templ.compile(minion_id='test.example.com', grains=grains)
