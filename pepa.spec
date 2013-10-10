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
#Requires: salt

%description
%{app}

%prep
mkdir -p %{buildroot}/srv/pepa %{buildroot}/usr/{bin,sbin} %{buildroot}/usr/share/man/{man1,man5} %{buildroot}/etc
tar zxvf %{sources}/%{name}.tar.gz -C %{buildroot}
cp %{sources}/conf/pepa.conf %{buildroot}/etc
cp %{sources}/*.1 %{buildroot}/usr/share/man/man1
cp %{sources}/*.5 %{buildroot}/usr/share/man/man5
ln -sf %{appdir}/bin/pepa %{buildroot}/usr/bin/pepa

%files
%defattr(-,root,root)
%dir %{appdir}
%{appdir}/*
%config(noreplace) /etc/pepa.conf
%dir /srv/pepa
/usr/bin/*
/usr/share/man/man1/*
/usr/share/man/man5/*
