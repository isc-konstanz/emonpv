#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import re
from os import path

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'pvprediction/', '__init__.py'), 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

# Get the long description from the README file
with open(path.join(here, 'README.md')) as f:
    readme = f.read()

setup(
    name='pvprediction',
    
    version=version,
    
    description='PV prediction provides a set functions to predict the yield of photovoltaic energy systems.',
    long_description=readme,
    
    author='Adrian Minde',
    author_email='adrian.minde@isc-konstanz.de',
    url='https://bitbucket.org/cossmic/pvprediction',
    
    packages=['pvprediction'],
    
    install_requires=['numpy >= 1.11.0',
                      'pandas >= 0.18.0',
                      'configparser >= 3.3.0',
#                       'cvxopt >= 1.1.7',
                      'pvlib >= 0.3.2'],
    
#     scripts=[path.join(here, 'bin/', 'pvyieldprediction')],
)