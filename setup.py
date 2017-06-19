#!/usr/bin/env python

"""Setup script for the 'control_flow' distribution."""

classifiers =  [
                'Intended Audience :: Developers',
                'Operating System :: OS Independent',
                'Programming Language :: Python :: 3.6',
                'Topic :: Software Development :: Code Generators',
                ]

# The rest in alphabetic order
ftp_url            = None
license            = 'GPL2'
maintainer         = "Rocky Bernstein"
maintainer_email   = "rb@dustyfeet.com"
modname            = 'control_flow'
name               = 'control_flow'
py_modules         = None
short_desc         = 'Control Flow Toolkit'
web                = 'https://github.com/rocky/python-control_flow/'

import os
def get_srcdir():
    filename = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
    return os.path.realpath(filename)

srcdir = get_srcdir()

def read(*rnames):
    return open(os.path.join(srcdir, *rnames)).read()

# Get info from files; set: long_description and VERSION
long_description   = ( read("README.rst") + '\n' )
exec(read('control_flow/version.py'))

from setuptools import setup, find_packages
setup(
       classifiers        = classifiers,
       description        = short_desc,
       install_requires   = ['click'],
       license            = license,
       long_description   = long_description,
       maintainer         = maintainer,
       maintainer_email   = maintainer_email,
       packages           = find_packages(),
       py_modules         = py_modules,
       name               = name,
       test_suite         = 'nose.collector',
       url                = web,
       tests_require     = ['nose>=1.0'],
       version            = VERSION)
