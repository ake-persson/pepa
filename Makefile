APP=pepa
NAME=${APP}
VERSION=0.1
PYTHON_VERSION=2.7
RELEASE=$(shell date -u +%Y%m%d%H%M)
SOURCE=https://github.com/mickep76/pepa.git
TMPDIR=.build
ARCH=`uname -p`
VENV=/opt/${APP}

all: rpm

req:
	yum install -y pandoc prelink rpm-build

venv:
	virtualenv -p python${PYTHON_VERSION} ${VENV}
	. ${VENV}/bin/activate
	${VENV}/bin/pip install -r requirements.txt
	( cd ${VENV} && rm -f lib64 && ln -s lib lib64 )
	virtualenv -p python${PYTHON_VERSION} --system-site-packages ${VENV}
	cp src/pepa.py ${VENV}/bin
#	prelink -u ${VENV}/bin/python
#	prelink -u ${VENV}/bin/python2.7
	tar -cvzf ${NAME}.tar.gz ${VENV}

rpm:	venv
	mkdir -p ${TMPDIR}/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
	pandoc -s -w man doc/pepa.1.md -o ${TMPDIR}/SOURCES/pepa.1
	pandoc -s -w man doc/pepa.conf.5.md -o ${TMPDIR}/SOURCES/pepa.conf.5
	cp -r ${NAME}.tar.gz conf ${TMPDIR}/SOURCES
	sed -e "s/%APP%/${APP}/g" -e "s/%VERSION%/${VERSION}/g" -e "s/%RELEASE%/${RELEASE}/g" -e "s/%PYTHON_VERSION%/${PYTHON_VERSION}/g" \
		-e "s!%SOURCE%!${SOURCE}!g" ${APP}.spec > ${TMPDIR}/SPECS/${NAME}.spec
	rpmbuild -vv -bb --target="${ARCH}" --clean --define "_topdir `pwd`/${TMPDIR}" ${TMPDIR}/SPECS/${NAME}.spec
	mv ${TMPDIR}/RPMS/${ARCH}/*.rpm .

clean:
	rm -f *.rpm *.tar.gz *.1 *.5
	rm -rf ${TMPDIR}
	rm -rf ${VENV}
