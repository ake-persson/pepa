%define app %APP%
%define name %{app}
%define version %VERSION%
%define release %RELEASE%
%define buildroot %{_topdir}/BUILDROOT
%define sources %{_topdir}/SOURCES
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
Requires: pepa

%description
%{app}

%pre
useradd -M -r -d /srv/pepa pepa || true

%prep
mkdir -p %{buildroot}/srv/pepa/{bin,.ssh}
cp %{sources}/files/id_dsa* %{buildroot}/srv/pepa/.ssh
cp %{sources}/bin/* %{buildroot}/srv/pepa/bin

%files
%defattr(-,pepa,pepa)
%dir /srv/pepa
%dir /srv/pepa/bin
%attr(0700,-,-) %dir /srv/pepa/.ssh
%attr(0755,-,-) /srv/pepa/bin/*
%attr(0600,-,-) /srv/pepa/.ssh/id_dsa
%attr(0644,-,-) /srv/pepa/.ssh/id_dsa.pub
