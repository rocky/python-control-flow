#!/usr/bin/bash
python_control_flow_owd=$(pwd)
bs=${BASH_SOURCE[0]}
mydir=$(dirname $bs)
python_control_flow_fulldir=$(readlink -f $mydir)
cd $python_control_flow_fulldir
. ./checkout_common.sh

pyenv_file="pyenv-newest-versions"
if ! source $pyenv_file ; then
    echo "Having trouble reading ${pyenv_file} version $(pwd)"
    exit 1
fi

cd ../dist/

install_check_command="python-cfg --version"
install_file="python_control_flow-1.0.0.tar.gz"
for version in $PYVERSIONS; do
    echo "*** Installing ${install_file} for Python ${version} ***"
    pyenv local $version
    pip install $install_file
    $install_check_command
    echo "----"
done
