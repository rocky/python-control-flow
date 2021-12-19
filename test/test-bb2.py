#!/usr/bin/env python
import sys
import os.path as osp
from control_flow.__main__ import doit

def testing():
    assert False, "This should have been replaced via read-in python script with a function called testing"

if len(sys.argv) == 1:
    print("You need to give a file name")
    sys.exit(1)
    pass

filename = sys.argv[1]
if filename.endswith(".py"):
    exec(open(filename).read())
    short = osp.basename(filename)[0:-3]
elif filename.endswith(".pyc"):
    short = osp.basename(filename)[0:-4]


doit(testing, short)  # NOQA
