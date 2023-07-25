#!/usr/bin/env python
import sys
import os.path as osp
from control_flow.__main__ import main
from glob import glob


def testing():
    assert (
        False
    ), "This should have been replaced via read-in python script with a function called testing"


if len(sys.argv) == 1:
    mydir = osp.dirname(osp.abspath(__file__))
    glob_path = mydir + "/../examples/*.py"
    files = glob(glob_path)
else:
    files = sys.argv[1:]
    pass

total = count = 0
for filename in files:

    # FIXME: redo with import module
    exec(open(filename).read())

    short = osp.basename(filename)[0:-3]

    main(testing, name=short)  # NOQA
    # cs.strip()
    # got = cs.strip()
    # want = expect().strip()  # NOQA
    if False:  # got != want:
        print("filename %s fails" % filename)
        # print(want)
        print("-" * 20)
        # print(got)
        pass
        sys.exit(1)
    else:
        print("filename %s" % filename)
        count += 1
        pass
    total += 1
    pass


print(f"{total} tests")
# print("%d tests, %d passed." % (total, count))
assert count == total
