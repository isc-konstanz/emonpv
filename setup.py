#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvforecast
    ~~~~~
    
    PV forecast provides a set of functions to forecast the energy generation of photovoltaic systems.
    To improve prediction performance, the recursive optimization of hourly efficiency values may be used.
    It utilizes the independent PVLIB toolbox, originally developed in MATLAB at Sandia National Laboratories,
    and can be found on GitHub "https://github.com/pvlib/pvlib-python".
    
"""
from os import path

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

here = path.abspath(path.dirname(__file__))


VERSION = '0.2.0'

DESCRIPTION = 'PV forecast provides a set of functions to forecast the energy generation of photovoltaic systems.'

# Get the long description from the README file
with open(path.join(here, 'README.md')) as f:
    README = f.read()

NAME = 'pvforecast'
LICENSE = 'GPLv3'
AUTHOR = 'ISC Konstanz'
MAINTAINER_EMAIL = 'adrian.minde@isc-konstanz.de'
URL = 'https://github.com/isc-konstanz/pvforecast'

INSTALL_REQUIRES = ['numpy >= 1.9.0',
                    'pandas >= 0.14.0',
                    'emonpy >= 0.1.2',
                    'pvlib >= 0.3.2']
#                   'cvxopt >= 1.1.7']

PACKAGES = ['pvforecast']

# SCRIPTS = ['bin/pvforecast']

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