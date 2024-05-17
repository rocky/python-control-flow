#!/bin/bash
# Run test-bb.py for Python 3.8 to 3.10
run_test_bb_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})
for version in 3.8 3.9 3.10 ; do
    echo === $version ===
    pyenv local $version && python ./test-bb.py
done
cd $test_version_owd
