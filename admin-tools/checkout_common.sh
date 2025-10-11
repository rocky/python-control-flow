# Common checkout routine
export PATH=$HOME/.pyenv/bin/pyenv:$PATH
bs=${BASH_SOURCE[0]}
mydir=$(dirname $bs)
python_control_flow_fulldir=$(readlink -f $mydir)

function setup_version {
    local repo=$1
    version=$2
    echo Running setup $version on $repo ...
    (cd ./$repo && . ./admin-tools/setup-${version}.sh)
    return $?
}

function checkout_finish {
    branch=$1
    cd $python_control_flow_fulldir/..
    cd $python_control_flow_owd
    git checkout $branch && pyenv local $PYTHON_VERSION && git pull
    rc=$?
    return $rc
}
