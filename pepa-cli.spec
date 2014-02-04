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

%description
%{app}

%prep
mkdir -p %{buildroot}/usr/bin %{buildroot}/usr/share/man/man1 %{buildroot}/etc/pepa
tar zxvf %{sources}/%{name}.tar.gz -C %{buildroot}
cp %{sources}/conf/pepa.conf %{buildroot}/etc/pepa
cp %{sources}/*.1 %{buildroot}/usr/share/man/man1
ln -sf %{appdir}/bin/pepa-cli.py %{buildroot}/usr/bin/pepa-cli

%files
%defattr(-,root,root)
%dir %{appdir}
%{appdir}/*
%config(noreplace) /etc/pepa/pepa.conf
/usr/bin/*
/usr/share/man/man1/*
