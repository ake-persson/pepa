APP=pepa-update
NAME=${APP}
VERSION=0.1
RELEASE=$(shell date -u +%Y%m%d%H%M)
SOURCE=git:project/rpm/pepa-default
TMPDIR=.build
ARCH=`uname -p`

all: rpm

rpm:
	mkdir -p ${TMPDIR}/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
	cp -r bin files ${TMPDIR}/SOURCES
	sed -e "s/%APP%/${APP}/g" -e "s/%VERSION%/${VERSION}/g" -e "s/%RELEASE%/${RELEASE}/g" \
		-e "s!%SOURCE%!${SOURCE}!g" ${APP}.spec > ${TMPDIR}/SPECS/${NAME}.spec
	rpmbuild -vv -bb --target="${ARCH}" --clean --define "_topdir `pwd`/${TMPDIR}" ${TMPDIR}/SPECS/${NAME}.spec
	mv ${TMPDIR}/RPMS/${ARCH}/*.rpm .

clean:
	rm -f *.rpm
	rm -rf ${TMPDIR}
