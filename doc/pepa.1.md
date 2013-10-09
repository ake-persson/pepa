% PEPA(1) Pepa Manual
% Michael Persson
% September 12, 2013

# NAME

pepa - generate configuration for Salt Stack

# SYNOPSIS

pepa *-h*|*--help*
pepa [*-c*|*--config* <file>] [*-d*|*--debug*] [*-n*|*--no-color*] [*-j*|*--json*] *--host* <hostname>

# DESCRIPTION

*pepa* generates configuration for Salt Stack in YAML or JSON using Hierarchical substitution similar to Hiera or Distill for Puppet, but with the additional support for Jinja.

# OPTIONS

-h, --help
:   Print help message.

-c, --config
:   Configuration file.

-d, --debug
:   Print debug information to STDERR.

-n, --no-color
:   Print output without colors.

-j, --json
:   Print configuration as JSON instead of YAML.

-h, --host
:   Host to generate configuration for.

# FILES

/etc/pepa.conf
:   Pepa configuration file.

/srv/pepa/inputs/
:   Pepa input files.

/srv/pepa/templates/
:   Pepa configuration templates.

# EXIT STATUS

0
    Success.

1
    Failure.


# AUTHOR

Michael Persson

# COPYING

Copyright 2013, Michael Persson, All rights reserved.
