# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""

__version__ = '0.0.1'

import logging
logging.basicConfig(level=logging.INFO)

from . import predict
from . import optimize
from . import systems
from . import forecast

from .emoncms import Emoncms