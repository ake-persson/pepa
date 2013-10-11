#!/bin/bash

USER=$( id -un )
GROUP='venvbuild'

sudo -i <<EOT
groupadd venvbuild
groupmems -g venvbuild -a ${USER}
chgrp venvbuild /opt
chmod 775 /opt
EOT

newgrp $GROUP
