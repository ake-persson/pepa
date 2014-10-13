#!/usr/bin/env bash

set -e
set -u

exit_code=0
for file in pepa/__init__.py scripts/pepa scripts/pepa-test; do
    echo $file
    pylint --rcfile .pylintrc $file || exit_code=1
done
exit $exit_code
