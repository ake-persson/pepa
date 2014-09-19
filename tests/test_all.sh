#!/usr/bin/env bash

set -e
set -u

for test in $( ls tests/*.{sh,py} | grep -v test_all.sh ); do
    printf "\n#### ${test} ####\n\n"
    $test
done
