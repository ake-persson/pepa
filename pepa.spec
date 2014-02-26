%define app %APP%
%define name %{app}
%define version %VERSION%
%define release %RELEASE%
%define buildroot %{_topdir}/BUILDROOT
%define sources %{_topdir}/SOURCES
%define appdir /opt/%{app}
%define python_version %PYTHON_VERSION%

BuildRoot: %{buildroot}
Source: %SOURCE%
Summary: %{app}
Name: %{name}
Version: %{version}
Release: %{release}
License: GPLv3 License
Group: System
AutoReqProv: no
Requires: mongodb-server uwsgi uwsgi-plugin-python nginx

%description
%{app}

%pre
useradd -M -r -d /srv/pepa pepa || true

%post
if ! [ -f '/etc/pepa/ssl/server.key' -a '/etc/pepa/ssl/server.crt' ]; then
    openssl genrsa -des3 -passout pass:x -out /etc/pepa/ssl/server.pass.key 2048
    openssl rsa -passin pass:x -in /etc/pepa/ssl/server.pass.key -out /etc/pepa/ssl/server.key
    rm -f /etc/pepa/ssl/server.pass.key
    openssl req -new -key /etc/pepa/ssl/server.key -out /etc/pepa/ssl/server.csr -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=$( hostname -s )"
    openssl x509 -req -days 365 -in /etc/pepa/ssl/server.csr -signkey /etc/pepa/ssl/server.key -out /etc/pepa/ssl/server.crt
fi
systemctl --system daemon-reload

%prep
mkdir -p %{buildroot}/srv/pepa %{buildroot}/usr/{bin,sbin} %{buildroot}/usr/share/man/{man1,man5} %{buildroot}/etc/pepa/ssl \
	%{buildroot}/usr/lib/systemd/system %{buildroot}/var/run/pepa %{buildroot}/etc/sysconfig %{buildroot}/etc/uwsgi.d \
	%{buildroot}/etc/nginx/conf.d
tar zxvf %{sources}/%{name}.tar.gz -C %{buildroot}
cp %{sources}/conf/uwsgi.ini %{buildroot}/etc/uwsgi.d/pepa.ini
cp %{sources}/conf/nginx.conf %{buildroot}/etc/nginx/conf.d/pepa.conf
cp %{sources}/conf/pepa.conf %{buildroot}/etc/pepa
cp %{sources}/files/pepa.service %{buildroot}/usr/lib/systemd/system
cp %{sources}/files/pepa %{buildroot}/etc/sysconfig
cp %{sources}/*.1 %{buildroot}/usr/share/man/man1
cp %{sources}/*.5 %{buildroot}/usr/share/man/man5
ln -sf %{appdir}/bin/pepa.py %{buildroot}/usr/sbin/pepa
ln -sf %{appdir}/bin/pepa-cli.py %{buildroot}/usr/bin/pepa-cli

%files
%defattr(-,root,root)
%dir %{appdir}
%{appdir}/*
%config(noreplace) /etc/pepa/pepa.conf
%attr(-,pepa,pepa) %dir /srv/pepa
/usr/bin/*
/usr/sbin/*
/usr/share/man/man1/*
/usr/share/man/man5/*
/usr/lib/systemd/system/*
%dir /etc/pepa/ssl
%attr(-,pepa,pepa) %dir /var/run/pepa
%config(noreplace) /etc/sysconfig/pepa
%config(noreplace) /etc/uwsgi.d/pepa.conf
%config(noreplace) /etc/nginx/conf.d/pepa.ini
