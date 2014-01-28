% PEPA(1) Pepa Manual
% Michael Persson
% September 12, 2013

# NAME

pepa.conf - pepa configuration file

# SYNOPSIS

/etc/pepa.conf

# DESCRIPTION

Configuration files for pepa.

# OPTIONS

[main]
:   Main section.

basedir
:   Basedir for pepa where input and templates are located, defaults to: /srv/pepa

environments
:   Environments available, defaults to: base

resources
:   Resources that can be accesses, defaults to: hosts

backend
:   Which backend to use for accessing templates can be either git or file, defaults to: file

[http]
:   HTTP section.

host
:   Which host address to listen to, defaults to: 0.0.0.0

port
:   Which port to listen to, defaults to: 5000

# RESOURCE

[hosts]
:   Host section.

key
:   Key for Schema

sequence
:   Susbstitution sequence for hosts.

# AUTHOR

Michael Persson

# COPYING

Copyright 2013, Michael Persson, All rights reserved.
