#!/usr/bin/bash
python_control_flow_owd=$(pwd)
bs=${BASH_SOURCE[0]}
mydir=$(dirname $bs)
python_control_flow_fulldir=$(readlink -f $mydir)
cd $python_control_flow_fulldir
. ./checkout_common.sh

cd ../dist/

for version in $PYVERSIONS; do
    echo $version
    pyenv local $version
    pip install python_control_flow_38-1.0.0.tar.gz;
    echo "----"
done
