#!/bin/bash
PYTHON_VERSION=3.8

python_control_flow_owd=$(pwd)
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

mydir=$(dirname $bs)
python_control_flow_fulldir=$(readlink -f $mydir)
. $mydir/checkout_common.sh

(cd $python_control_flow_fulldir/../.. && setup_version x-python master)
checkout_finish python-3.8-to-3.10
