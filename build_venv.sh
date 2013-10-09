#!/bin/bash

USER=$( id -un )

sudo -i <<EOT
groupadd venvbuild
groupmems -g venvbuild -a ${USER}
chgrp venvbuild /opt
chmod 775 /opt
EOT
