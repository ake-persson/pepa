APP=pepa
NAME=${APP}
VERSION=0.4.5
PYTHON_VERSION=2.7
RELEASE=$(shell date -u +%Y%m%d%H%M)
SOURCE=https://github.com/mickep76/pepa.git
TMPDIR=.build
ARCH=`uname -p`
VENV=/opt/${APP}

all: rpm

venv:
	virtualenv -p python${PYTHON_VERSION} ${VENV} --no-site-packages
	. ${VENV}/bin/activate
	${VENV}/bin/pip install -r requirements.txt
	( cd ${VENV} && rm -f lib64 && ln -s lib lib64 )
	sed "s!/usr/bin/env python!${VENV}/bin/python2!" src/pepa.py >${VENV}/bin/pepa.py
	sed "s!/usr/bin/env python!${VENV}/bin/python2!" src/pepa-cli.py >${VENV}/bin/pepa-cli.py
	sed "s!/usr/bin/env python!${VENV}/bin/python2!" src/export.py >${VENV}/bin/export.py
	sed "s!/usr/bin/env python!${VENV}/bin/python2!" src/import.py >${VENV}/bin/import.py
	chmod 755 ${VENV}/bin/pepa.py
	chmod 755 ${VENV}/bin/pepa-cli.py
	chmod 755 ${VENV}/bin/export.py
	chmod 755 ${VENV}/bin/import.py
	prelink -u ${VENV}/bin/python2.7 || true
	tar -cvzf ${NAME}.tar.gz ${VENV}

rpm: venv
	mkdir -p ${TMPDIR}/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
	pandoc -s -w man doc/pepa.1.md -o ${TMPDIR}/SOURCES/pepa.1
	pandoc -s -w man doc/pepa.conf.5.md -o ${TMPDIR}/SOURCES/pepa.conf.5
	cp -r ${NAME}.tar.gz conf files ${TMPDIR}/SOURCES
	sed -e "s/%APP%/${APP}/g" -e "s/%VERSION%/${VERSION}/g" -e "s/%RELEASE%/${RELEASE}/g" -e "s/%PYTHON_VERSION%/${PYTHON_VERSION}/g" \
		-e "s!%SOURCE%!${SOURCE}!g" ${APP}.spec > ${TMPDIR}/SPECS/${NAME}.spec
	rpmbuild -vv -bb --target="${ARCH}" --clean --define "_topdir `pwd`/${TMPDIR}" ${TMPDIR}/SPECS/${NAME}.spec
	mv ${TMPDIR}/RPMS/${ARCH}/*.rpm .

clean:
	rm -f *.rpm *.tar.gz *.1 *.5
	rm -rf ${TMPDIR}
	rm -rf ${VENV}
