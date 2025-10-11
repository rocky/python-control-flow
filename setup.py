#!/usr/bin/env python

"""Setup script for the 'control_flow' distribution."""

import io
import os
from setuptools import setup, find_packages

classifiers = [
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Code Generators",
]

# The rest in alphabetic order
entry_points = {"console_scripts": ["python-cfg=control_flow.__main__:main"]}
ftp_url = None
license = "GPL2"
maintainer = "Rocky Bernstein"
maintainer_email = "rb@dustyfeet.com"
modname = "python_control_flow"
name = "python-control-flow"
py_modules = ["python_control_flow"]
short_desc = "Control Flow Toolkit"
web = "https://github.com/rocky/python-control-flow"


def get_srcdir():
    filename = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
    return os.path.realpath(filename)


srcdir = get_srcdir()


def read(*rnames, encoding="utf-8"):
    """Read a file relative to the project root using a predictable encoding.

    Using io.open with utf-8 guarantees consistent behavior during wheel
    creation and on different platforms when setup.py is executed by build
    backends.
    """
    with io.open(os.path.join(srcdir, *rnames), "r", encoding=encoding) as f:
        return f.read()


# Get info from files; set: long_description and VERSION
# Readme text used for the long_description which will be embedded into the
# wheel metadata. Make sure encoding is explicit so that builders don't skip
# it due to decode errors.
long_description = read("README.rst") + "\n"

# Version is overwritten by the below exec(read())
__version__ = "??"
exec(read("python_control_flow/version.py"))


setup(
    classifiers=classifiers,
    description=short_desc,
    entry_points=entry_points,
    install_requires=["click", "xdis >= 6.1.1"],
    license=license,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    maintainer=maintainer,
    maintainer_email=maintainer_email,
    packages=find_packages(),
    py_modules=py_modules,
    name=name,
    test_suite="nose.collector",
    url=web,
    tests_require=["nose>=1.0"],
    version=__version__,
)
