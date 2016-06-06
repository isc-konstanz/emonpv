# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
    PV prediction provides a set of functions to predict the yield and generation of photovoltaic system.
    To improve the prediction performance, the recursive optimization of hourly efficiency values may be used.
    It utilizes the independent PVLIB toolbox, originally developed in MATLAB at Sandia National Laboratories,
    and can be found on GitHub "https://github.com/pvlib/pvlib-python".
    
"""

__version__ = '0.1.1'

import logging
logging.basicConfig(level=logging.INFO)

from . import predict

from . import system
from .system import System

from . import weather
from .weather import Weather
