#!/bin/bash
PACKAGE="python_control_flow"

# FIXME put some of the below in a common routine
function finish {
  if [[ -n "$make_dist_trepanxpy_newest_owd" ]] then
     cd $make_dist_trepan_xpy_newest_owd
  fi
}

make_dist_python_control_flow_38_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})
trap finish EXIT

if ! source ./pyenv-3.8-3.10-versions ; then
    exit $?
fi

if ! source ./setup-python-3.8.sh ; then
    exit $?
fi

cd ..

source ${PACKAGE}/version.py
if [[ ! -n $__version__ ]]; then
    echo "Something is wrong: __version__ should have been set."
    exit 1
fi
echo $__version__

for pyversion in $PYVERSIONS; do
    echo --- $pyversion ---
    if [[ ${pyversion:0:4} == "pypy" ]] ; then
	echo "$pyversion - PyPy does not get special packaging"
	continue
    fi
    if ! pyenv local $pyversion ; then
	exit $?
    fi
    # pip bdist_egg create too-general wheels. So
    # we narrow that by moving the generated wheel.

    # Pick out first two number of version, e.g. 3.5.1 -> 35
    first_two=$(echo $pyversion | cut -d'.' -f 1-2 | sed -e 's/\.//')
    rm -fr build
    python setup.py bdist_wheel
    mv -v dist/${PACKAGE}-$__version__-{py3,py$first_two}-none-any.whl
done

python ./setup.py sdist
tarball=dist/${PACKAGE}-${__version__}.tar.gz

if [[ -f $tarball ]]; then
    mv -v $tarball dist/${PACKAGE}_38-${__version__}.tar.gz
fi
finish
