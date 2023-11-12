#!/usr/bin/env python

"""Setup script for the 'control_flow' distribution."""

import os
from setuptools import setup, find_packages

classifiers = [
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Topic :: Software Development :: Code Generators",
]

# The rest in alphabetic order
entry_points = {"console_scripts": ["python-cfg=control_flow.__main__:main"]}
ftp_url = None
license = "GPL2"
maintainer = "Rocky Bernstein"
maintainer_email = "rb@dustyfeet.com"
modname = "control_flow"
name = "control_flow"
py_modules = "control_flow"
short_desc = "Control Flow Toolkit"
web = "https://github.com/rocky/python-control_flow/"


def get_srcdir():
    filename = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
    return os.path.realpath(filename)


srcdir = get_srcdir()


def read(*rnames):
    return open(os.path.join(srcdir, *rnames)).read()


# Get info from files; set: long_description and VERSION
long_description = read("README.rst") + "\n"
exec(read("control_flow/version.py"))


setup(
    classifiers=classifiers,
    description=short_desc,
    entry_points=entry_points,
    install_requires=["click", "xdis >= 6.0.3"],
    license=license,
    long_description=long_description,
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
