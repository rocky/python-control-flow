#/bin/bash
python_control_flow_merge_38_owd=$(pwd)
PYTHON_VERSION=3.8
pyenv local $PYTHON_VERSION
cd $(dirname ${BASH_SOURCE[0]})
if . ./setup-python-3.8.sh; then
    git merge master
fi
cd $python_control_flow_merge_38_owd
