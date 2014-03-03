FROM mattdm/fedora-small:f19

# Setup local repositories
#RUN rm -f /etc/yum.repos.d/*
#ADD local.repo /etc/yum.repos.d/local.repo

# Update and install pre-requisites
RUN yum update -y; \
yum install -y python; \
yum clean all

# Create template folder
RUN mkdir -p /srv/pepa

# Add Python requirements
ADD requirements.txt /root/requirements.txt

# Build and cleanup in one go, too minimise image size
RUN yum install --downloadonly python-devel python-pip gcc openldap openldap-devel openssl openssl-devel libffi libffi-devel; \
find /var/cache/yum -name *.rpm | sed -e 's!.*/!!' -e 's!.rpm$!!' >/root/build_dependencies.txt; \
yum install -y python-devel python-pip gcc openldap openldap-devel openssl openssl-devel libffi libffi-devel; \
#export https_proxy=https://<proxy>:<port>; \
pip install -r /root/requirements.txt; \
rpm -e --nodeps $( cat /root/build_dependencies.txt ); \
yum clean all

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
