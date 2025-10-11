#!/bin/bash
PYTHON_VERSION=3.13

python_control_flow_owd=$(pwd)
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

mydir=$(dirname $bs)
python_control_flow_fulldir=$(readlink -f $mydir)
. ${python_control_flow_fulldir}/checkout_common.sh

(cd ${python_control_flow_fulldir}/../.. && setup_version python-xdis master)
checkout_finish master
