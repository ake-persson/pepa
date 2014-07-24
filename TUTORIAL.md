# Installing Salt'n'Pepa

## Install SaltStack and Python modules

## Fedora

```bash
sudo yum install salt-minion salt-master
sudo yum install python-pip PyYAML python-jinja2 python-logging python-pygments
sudo pip install argparse colorlog
```

## Ubuntu

```bash
sudo add-apt-repository ppa:saltstack/salt
sudo apt-get update
sudo apt-get install salt-minion salt-master
# TBD: install modules
```

## Mac OS X

First you need to install Xcode Command Line tools.

```bash
sudo easy_install pip
sudo pip install salt pyyaml jinja2 argparse logging colorlog pygments
```

## Other

```bash
sudo pip install salt pyyaml jinja2 argparse logging colorlog pygments
```

## Install Pepa

```bash
sudo mkdir -p /srv/salt/ext/pillar
git clone git@github.com:mickep76/pepa.git
sudo cp pepa/pepa.py /srv/salt/ext/pillar
```

Verify you have the required Python modules for Pepa.

```bash
cd pepa
./pepa.py -c examples/master test.example.com -d
```

# Configuring Salt'n'Pepa

Here is a Salt Master setup with 3 environments base, qa and prod.

**/etc/salt/minion**

```yaml
master: <hostname>
```

*Obv. you need to replace \<hostname\>*

**/etc/salt/master**

```yaml
# Accept ANY host automatically
auto_accept: True

# Path for states
file_roots:
  base:
	- /srv/salt/base/states
  qa:
    - /srv/salt/qa/states
  prod:
	- /srv/salt/prod/states

# Path for pillars
pillar_roots:
  base:
	- /srv/salt/base/pillars
  qa:
    - /srv/salt/qa/pillars
  prod:
	- /srv/salt/prod/pillars

# Path to ext. pillars
extension_modules: /srv/salt/ext

# Configuration for ext. pillar Pepa
ext_pillar:
  - pepa:
	  resource: hosts
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

# Delimiter used in Pepa templates for nested keys
pepa_delimiter: ..

# Include Pepa sub key in pillar output
pepa_subkey: True

# Path for Pepa templates
pepa_roots:
  base: /srv/salt/base
  qa: /srv/salt/qa
  prod: /srv/salt/prod

# Enable debug
#log_level: debug

# Enable debug, only for Pepa
# Requires "log_level: debug" to be set
#log_granular_levels:
#  salt: warning
#  salt.loaded.ext.pillar.pepa: debug
```

# Create Git repository

Create a Git repository on GitHub. Clone it and do the initial commit.

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
mkdir {states,pillar,hosts}
mkdir hosts/{default,host_input,environment,region,country,os,roles,host}
touch pillar/top.sls states/top.sls
git add states pillar
git commit -am'Added initial skeleton'
```

*Git won't add empty folders.*

## Add script for Git clone/pull

**/usr/bin/salt-update**

```bash
#!/bin/bash

set -e
set -u

source /etc/salt/salt-update.conf

export GIT_SSH="/usr/bin/salt-update-git-ssh"

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

**/usr/bin/salt-update-git-ssh**

```bash
#!/bin/bash

set -e
set -u

source /etc/salt/salt-update.conf

exec /usr/bin/ssh -i $SSH_KEY -p $PORT -o LogLevel=quiet -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "$@"
```

**/etc/salt/salt-update.conf**

```bash
readonly USER='git'
readonly BASEDIR='/srv/salt'
readonly CONFDIR='/etc/salt'
readonly SSH_KEY="${CONFDIR}/.ssh/id_dsa"
readonly URI='<uri>'
```

*Obv. you have to replace \<uri\> with the uri to your Git repository*

Enable scrips as executable.

```bash
chmod +x /usr/bin/salt-update
chmod +x /usr/bin/salt-update-git-ssh
```

## Create ssh key for Github

```bash
sudo mkdir /etc/salt/.ssh
sudo chmod 700 /etc/salt/.ssh
sudo ssh-keygen -t dsa -f /etc/salt/.ssh/id_dsa
```

*Create the key without a password*

Once you have created the SSH key add it to Deploy Keys in repository Settings.

# Clone Git repository

You should now be able to Clone/Pull the repository.

```bash
sudo salt-update
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

This is normally done automatically after sucessfull tests, using a CI build server such as [Jenkins](http://jenkins-ci.org/).

# Pepa templates

Since you can chain Ext. Pillars Pepa can either be used for per host input or you can pull information from Cobbler or other system. This would require that you write your own Ext. Pillar.

My recommendation would be to keep the info. as a Template and then populate other systems such as Cobbler using this.

If you have external information you wan't to use in the hierarchical substitution you need to import them in the Default template. You can access both Grains and Pillars using Jinja like "{{ grains.osfinger }}" or "{{ pillar.region }}".

**hosts/default/default.yaml**

```yaml
network..dns..search:
  - example.com
network..dns..options:
  - timeout:2
  - attempts:1
  - ndots:1
osfinger: {{ grains.osfinger }}
salt..version: 2014.1.5
salt..release: 1
salt..master: salt.example.com
```

Here is an example of a per host template.

**hosts/host_input/test_example_com.yaml**

```yaml
location..region: emea
location..country: nl
location..datacenter: foobar
environment: dev
roles:
  - salt.master
network..gateway: 10.0.0.254
network..interfaces..eth0..hwaddr: 00:20:26:a1:12:12
network..interfaces..eth0..dhcp: False
network..interfaces..eth0..ipv4: 10.0.0.3
network..interfaces..eth0..netmask: 255.255.255.0
network..interfaces..eth0..fqdn: {{ hostname }}
cobbler..profile: fedora-19-x86_64
```

*All extended characters in filenames are converted to underscore.*

**hosts/region/amer.yaml**

```yaml
network..dns..servers:
  - 10.0.0.1
  - 10.0.0.2
time..ntp..servers:
  - ntp1.amer.example.com
  - ntp2.amer.example.com
  - ntp3.amer.example.com
time..timezone: America/Chihuahua
```

So the templates are run in the order specified in the salt master configuration file.

    default -> host_input -> environment -> region -> country -> os -> roles -> host

This allow's for Hierarhical Substitution, additionally to this you have access to Jinja and Grains/Pillars.

Host input and host overrides are not staged since they are directly host related. To control if a category is staged, this can done with the configuration entry "base_only".

# Salt States

Here are some examples for configuring time on a Fedora host.

**states/timezone/init.sls**

```yaml
timezone:
  module.run:
    - name: timezone.set_zone
    - timezone: {{ pillar.time.timezone }}
  file.managed:
    - name: /etc/sysconfig/clock
    - user: root
    - group: root
    - mode: '0644'
    - source: salt://timezone/files/clock.jinja
    - template: jinja
```

**states/timezone/files/clock.jinja**

```yaml
ZONE="{{ pillar.time.timezone }}"
UTC=true
```

**states/ntpdate/init.sls**

```yaml
include:
  - timezone

ntpdate:
  pkg.installed:
  file.managed:
    - name: /etc/sysconfig/ntpdate
    - user: root
    - group: root
    - mode: '0644'
    - source: salt://ntpdate/files/ntpdate.jinja
    - template: jinja
    - require:
      - pkg: ntpdate
```

**states/ntpdate/files/ntpdate.jinja**

```yaml
OPTIONS="-p2 -b {{ pillar.time.ntp.servers | join(' ') }}"
RETRIES=2
SYNC_HWCLOCK=yes
```

**states/ntp/init.sls**

```yaml
include:
  - ntpdate

ntp:
  pkg.installed:
  file.managed:
    - name: /etc/ntp.conf
    - user: root
    - group: root
    - mode: '0644'
    - source: salt://ntp/files/ntp.conf.jinja
    - template: jinja
    - require:
      - pkg: ntp
  service.running:
    - name: ntpd
    - enable: True
    - reload: True
    - watch:
      - file: ntp
    - require:
      - pkg: ntp
```

**states/ntp/files/ntp.conf.jinja**

```yaml
{% for server in pillar.time.ntp.servers %}
server {{ server }} minpoll 3 maxpoll 7
{%- endfor %}

driftfile /var/lib/ntp/drift

enable stats
statsdir /var/log/ntpstats/
statistics loopstats peerstats
```

# Configure top.sls

Here is an example top.sls file for states, you can see that roles are included as if they we're states. This make's it very easy to include states without modifying the top.sls file.

**states/top.sls**

```yaml
base:
  'environment:base':
    - match: pillar
    - ntp
{%- if pillar['roles'] is defined %}
{%- for role in pillar['roles'] %}
    - {{ role }}
{%- endfor %}
{%- endif %}

qa:
  'environment:qa':
    - match: pillar
    - ntp
{%- if pillar['roles'] is defined %}
{%- for role in pillar['roles'] %}
    - {{ role }}
{%- endfor %}
{%- endif %}

prod:
  'environment:prod':
    - match: pillar
    - ntp
{%- if pillar['roles'] is defined %}
{%- for role in pillar['roles'] %}
    - {{ role }}
{%- endfor %}
{%- endif %}
```