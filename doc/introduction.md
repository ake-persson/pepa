# Pepa

## Introduction

### File structure

**Example file structure:**
<pre>
/srv/pepa/
	base/	(Environment: base)
		hosts/	(Resource: hosts)
			inputs/
				foobar.example.com.json
		schemas/	(Resource: schemas)
			inputs/	(Input for host resources)
				hosts.json
				users.json
		users/
			inputs/
				jode.json
				bgates.json
			templates/
				default/
					default.json
	dev/	(Environment: dev)
		hosts/
			templates/	(Templates for host resources)
				default/
					default.json
				region/
					emea.json
					amer.json
...
</pre>

### Inputs

Inputs are the authoritative values for a host, these values can then be used for hierarchical substitution or using Jinja templating.

**Example input file:**
<pre>
hostname: foobar.example.com
region: amer
country: us
environment: dev
roles:
- server
</pre>

### Schemas

JSON schemas are used for validating input, that it adheres to the data model. This means that if you wan't to add additional attributes, you only need to modify the JSON schema.

This is also used for defining the CLI, so if you add a new attribute this will automatically be included as an option in the CLI.

**Example JSON schema:**
<pre>
{
    "title": "Host validation",
    "id": "hostname",
    "type": "object",
    "properties": {
        "hostname": {
            "type": "string",
            "format": "host-name",
            "description": "Hostname for this host",
            "pattern": "^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\\.)+[a-zA-Z]{2,6}$"
        },
	}
}
</pre>

[JSON schema](http://json-schema.org/)

[JSON schema generator](http://www.jsonschema.net/)

### Templates

Templates are used for Hierarchical substitution to create a complete configuration for a resource.

A simple hierarchy can look like this:

Default -> Region -> Country -> Environment -> Roles -> Host

This means templates are parsed in this order and values are substituted.

**Example template:**
<pre>
ntp_servers:
- ntp1.example.com
- ntp2.example.com
- ntp3.example.com
smtp_server: smtp.{{region}}.example.com
dns_servers:
- 192.168.1.1
- 192.168.1.2
dns_search:
- example.com
- emea.example.com
- amer.example.com
</pre>

### Jinja

In the example above you probably recognised the following:

<pre>
smtp_server: smtp.{{region}}.example.com
</pre>

This is not using substitution but rather Jinja which is a web templating language. That replaces {{region}} with the content of that variable.

Jinja can be used for some quite advanced templating using simple language constructs.

[Jinja2](http://jinja.pocoo.org/docs/)

## REST API

Pepa comes equipped with a REST API for CRUD (create, read, update, delete) operations on resources.

**Get all hosts:**
<pre>
curl -i http://localhost:8080/hosts
</pre>

**Get host:**
<pre>
curl -i http://localhost:8080/hosts/foobar.example.com
</pre>

**Create host:**
<pre>
read -d '' yaml &lt;&lt;__EOT__
country: us
environment: dev
hostname: foobar.example.com
region: amer
roles:
- server
__EOT__

curl -i -u user:password -X POST -H "Accept: application/yaml" -H "Content-Type: application/yaml" -d "${yaml}" http://localhost:8080/hosts
</pre>

**Update host:**
<pre>
read -d '' yaml &lt;&lt;__EOT__
region: apac
country: au
__EOT__

curl -i -u user:password -X PATCH -H "Accept: application/yaml" -H "Content-Type: application/yaml" -d "${yaml}" http://localhost:8080/hosts/foobar.example.com
</pre>

**Delete host:**
<pre>
curl -i -u user:password -X DELETE http://localhost:8080/hosts/foobar.example.com
</pre>

## CLI

**List resources:**
<pre>
./pepa-cli.py list schemas --fields schema
</pre>

**Help for resource:**
<pre>
./pepa-cli.py list|get|add|modify|delete hosts --help
./pepa-cli.py list|get|add|modify|delete users --help
</pre>

**List resource:**
This will list resources as a formatted Table.

Arguments:
<pre>
--format json|yaml|table|text|csv
--fields list of fields
</pre>

This will list resources as a formatted Table.
<pre>
./pepa-cli.py list hosts --format table --fields hostname,region,country,environment
+--------------------+--------+---------+-------------+
|      hostname      | region | country | environment |
+--------------------+--------+---------+-------------+
| foobar.example.com |  amer  |    us   |     dev     |
+--------------------+--------+---------+-------------+
</pre>

This will list resources as a formatted CSV.
<pre>
./pepa-cli.py list hosts --format csv --fields hostname,region,country,environment
"hostname","region","country","environment"
"foobar.example.com","amer","us","dev"
</pre>

**Add resource:**
<pre>
./pepa-cli.py add hosts spider.example.com -e dev -r amer -c us
Password: ********
country: us
environment: dev
hostname: spider.example.com
region: amer
success: true
</pre>

**Get resource:**
<pre>
./pepa-cli.py get hosts spider.example.com
spider.example.com
country: us
environment: dev
hostname: spider.example.com
region: amer
</pre>

**Modify resource:**
<pre>
./pepa-cli.py modify hosts spider.example.com -r emea -c nl
Password: ********
country: nl
environment: dev
hostname: spider.example.com
region: emea
success: true
</pre>

**Delete resource:**
<pre>
./pepa-cli.py delete hosts spider.example.com
Password: ********
</pre>