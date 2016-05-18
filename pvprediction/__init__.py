# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""

__version__ = '0.0.8'

import logging
logging.basicConfig(level=logging.INFO)

from . import predict
from . import systems
from . import weather