# Installing Salt'n'Pepa

This Guide assumes you're using Fedora/RedHat/CentOS.

## Install SaltStack

```bash
sudo yum install salt-minion salt-master
```

## Install Pepa

```bash
sudo yum install python-pip PyYAML python-jinja2 python-logging python-pygments
sudo pip install argparse colorlog
```

Alt. using only pip.

```bash
sudo yum install python-pip
sudo pip install pyyaml jinja2 argparse logging colorlog pygments
```

```bash
sudo mkdir -p /srv/salt/ext/pillar
git clone git@github.com:mickep76/pepa.git
sudo cp pepa/pepa.py /srv/salt/ext/pillar
```

# Configuring Salt'n'Pepa

Here is a setup with 3 environments base, qa and prod.

**/etc/salt/minion**

```yaml
master: <hostname>
```

**/etc/salt/master**

```yaml
auto_accept: True

file_roots:
  base:
	- /srv/salt/base/states
  qa:
    - /srv/salt/qa/states
  prod:
	- /srv/salt/prod/states

pillar_roots:
  base:
	- /srv/salt/base/pillars
  qa:
    - /srv/salt/qa/pillars
  prod:
	- /srv/salt/prod/pillars

extension_modules: /srv/salt/ext

ext_pillar:
  - pepa:
	  resource: host
	  sequence:
		- default:
		- hostname:
			name: host_input
			base_only: True
		- environment:
		- location..region:
			name: region
		- location..country:
			name: country
		- osfinger:
		    name: os
		- roles:
		- hostname:
			name: host
			base_only: True

pepa_delimiter: ..
pepa_subkey: True
pepa_roots:
  base: /srv/salt/base
  qa: /srv/salt/qa
  prod: /srv/salt/prod

#log_level: debug

#log_granular_levels:
#  salt: warning
#  salt.loaded.ext.pillar.pepa: debug
```

# Creating Git repository

Create a Git repository on GitHub.

```bash
git clone <uri>
cd salt
touch README.md
git add README.md
git commit -am'Added README file'
git push -u origin master
```

Create skeleton for Salt'n'Pepa.

```bash
mkdir {states,pillar,host}
mkdir hosts/{default,host_input,environment,region,country,os,roles,host}
touch pillars/top.sls states/top.sls
```

**/usr/local/bin/salt-update**

```bash
#!/bin/bash

set -e
set -u

source /etc/sysconfig/salt-update

export GIT_SSH="/usr/local/bin/salt-update-git-ssh"

sync() {
	local uri="$1" branch="$2" dir="$3"

	echo "# Sync branch ${branch} to ${dir}"
	if [ -d ${dir}/.git ]; then
		( cd $dir; git reset --hard origin/${branch}; git clean -fd; git pull )
	else
		rm -rf ${dir}
		git clone -b ${branch} ${uri} ${dir}
	fi
	echo
}

mkdir -p ${BASEDIR}
sync ${USER}@${URI} master ${BASEDIR}/base
for env in ${ENVIRONMENTS}; do
	sync ${USER}@${URI} ${env} ${BASEDIR}/${env}
done
```

**/usr/local/bin/salt-update-git-ssh**

```bash
#!/bin/bash

set -e
set -u

source /etc/sysconfig/salt-update

exec /usr/bin/ssh -i $SSH_KEY -p $PORT -o LogLevel=quiet -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "$@"
```

**/etc/sysconfig/salt-update**

```bash
readonly USER='git'
readonly BASEDIR='/srv/salt'
readonly CONFDIR='/etc/salt'
readonly SSH_KEY="${CONFDIR}/.ssh/id_dsa"
readonly URI='<uri>'
```

```bash
chmod +x /usr/local/bin/salt-update
chmod +x /usr/local/bin/salt-update-ssh-git
```

# Setting up staging

In order to facilitate testing we need to stage our changes. The easiest way to do this is to create a separate Branch in Git for each environment.

```bash
git clone <uri>
cd salt
vi .gitattributes
```

**.gitattributes**

```
states/top.sls merge=ours
pillars/top.sls merge=ours
```

```bash
git commit -am'Excluded top.sls and inputs from merging'
```

## Create QA branch

```bash
git branch qa
git checkout qa
echo >states/top.sls
echo >pillars/top.sls
git commit -am'Empty top.sls for Pillars and States'
git push -u origin qa
```

## Create Prod branch

```bash
git checkout qa
git branch prod
git push -u origin prod
```

## Stage changes

### Enable ours merging strategy.

If you intend to do merging on a checkout, you need to do this step. Otherwise you will merge top.sls files.

```bash
git config merge.ours.driver true
```

### Merge master/base to qa.

```bash
git checkout qa
git merge master
git push
git checkout master
```

### Merge qa to prod.

```bash
git checkout prod
git merge qa
git push
git checkout master
```