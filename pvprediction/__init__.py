# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""

__version__ = '0.0.0.dev1'

import logging
logging.basicConfig()

from .prediction import get_yield_prediction
from .prediction import get_power_prediction
from .prediction import get_prediction
from .systems import get_systems