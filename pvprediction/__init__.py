# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""

__version__ = '0.0.1'

import logging
logging.basicConfig(level=logging.INFO)

from . import predict
from . import systems
from . import irradiation

from .emoncms import Emoncms