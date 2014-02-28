FROM mattdm/fedora-small:f19

# Setup local repositories
#RUN rm -f /etc/yum.repos.d/*
#ADD local.repo /etc/yum.repos.d/local.repo

# Create template folder
RUN mkdir -p /srv/pepa

# Build Pepa
RUN yum install -y python python-devel python-pip gcc openldap openldap-devel openssl openssl-devel libffi libffi-devel
ADD requirements.txt /srv/pepa/requirements.txt
RUN pip install -r /srv/pepa/requirements.txt
#RUN export https_proxy=https://<proxy>:<port> && pip install -r /srv/pepa/requirements.txt

# Add source
ADD src/pepa.py /usr/sbin/pepa
ADD src/import.py /usr/sbin/pepa-import
ADD src/export.py /usr/sbin/pepa-export
ADD src/pepa-cli.py /usr/bin/pepa-cli

# Add configuration
RUN mkdir -p /etc/pepa/ssl
ADD conf/pepa-docker.conf /etc/pepa/pepa.conf

# Add examples
ADD example/base /srv/pepa/base
ADD example/dev /srv/pepa/dev

# Expose the port and start Pepa
EXPOSE 8080
CMD /usr/sbin/pepa
