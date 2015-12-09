# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""

__version__ = '0.0.0.dev1'

import logging
logging.basicConfig()

from . import prediction
from . import optimisation
from . import systems

from .emoncms import Emoncms