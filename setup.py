#!/usr/bin/env python

"""Setup script for the 'python-control-flow' distribution."""

import sys
from setuptools import setup

major = sys.version_info[0]
minor = sys.version_info[1]

if major != 3 or not minor >= 11:
    sys.stderr.write(
        "This installation medium is only for Python 3.11 and later. You are running Python %s.%s.\n"
        % (major, minor)
    )

if major == 3 and 8 <= minor <= 10:
    sys.stderr.write(
        "Please install using python-control-flow_38-x.y.z.tar.gz from https://github.com/rocky/python-control-flow/releases\n"
    )
    sys.exit(1)
else:
    sys.stderr.write("Please install using an older release\n")
    sys.exit(1)

setup()
