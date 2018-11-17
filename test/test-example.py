#!/usr/bin/env python
import sys
import os.path as osp
from control_flow.main import doit
from glob import glob



if len(sys.argv) == 0:
    mydir = osp.normpath(osp.dirname(__file__))
    files = glob.glob(mydir + '/examples/*.py')
else:
    files = sys.argv[1:]

for filename in files:

    # FIXME: redo with import module
    exec(open(filename).read())

    short = osp.basename(filename)[0:-3]

    cs = doit(testing, short)  # NOQA
    got = cs.strip()
    want = expect().strip()  # NOQA
    if got != want:
        print(want)
        print('-' * 20)
        print(got)
        pass
    assert want == got
    pass
