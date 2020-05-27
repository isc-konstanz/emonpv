#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    emonpv
    ~~~~~~
    
    EmonPV provides a set of functions to calculate the energy yield of photovoltaic systems.
    It utilizes the independent pvlib toolbox, originally developed in MATLAB at Sandia National Laboratories,
    and can be found on GitHub "https://github.com/pvlib/pvlib-python".
    
"""
from os import path

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

here = path.abspath(path.dirname(__file__))
info = {}
with open(path.join("emonpv", "_version.py")) as f: exec(f.read(), info)

VERSION = info['__version__']

DESCRIPTION = 'EmonPV provides a set of functions to calculate the energy yield of photovoltaic systems.'

# Get the long description from the README file
with open(path.join(here, 'README.md')) as f:
    README = f.read()

NAME = 'emonpv'
LICENSE = 'GPLv3'
AUTHOR = 'ISC Konstanz'
MAINTAINER_EMAIL = 'adrian.minde@isc-konstanz.de'
URL = 'https://github.com/isc-konstanz/emonpv'

INSTALL_REQUIRES = ['numpy',
                    'pandas',
                    'pvlib >= 0.3.2',
                    'core >= 0.1.2']

PACKAGES = ['emonpv']

# SCRIPTS = ['bin/emonpv']

SETUPTOOLS_KWARGS = {
    'zip_safe': False,
    'scripts': [],
    'include_package_data': True
}

setup(
    name = NAME,
    version = VERSION,
    license = LICENSE,
    description = DESCRIPTION,
    long_description=README,
    author = AUTHOR,
    author_email = MAINTAINER_EMAIL,
    url = URL,
    packages = PACKAGES,
    install_requires = INSTALL_REQUIRES,
    **SETUPTOOLS_KWARGS
)