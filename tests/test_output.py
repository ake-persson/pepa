#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import subprocess
import sys

# Validate importing Pepa

# Validate calling Pepa from TTY
expected = yaml.load(open('./output.yaml').read())
proc = subprocess.Popen(['./pepa.py', '--config', 'examples/master', 'test.example.com'], cwd='..', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
actual = yaml.load(proc.communicate()[0])

if cmp(expected, actual) == 0:
  print "SUCCESS!"
  sys.exit(0)
else:
  print "FAILED!"
  sys.exit(1)
