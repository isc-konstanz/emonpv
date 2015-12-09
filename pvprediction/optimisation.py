#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import numpy as np
import pandas as pd
from pvprediction import prediction
    
    
def systemsparam(system, forecast, reference):
    data = pd.DataFrame(data=np.nan, index=forecast.index, columns=['estimate', 'innovation'])
    data['estimate'] = prediction.systempower(system, forecast)
    
    data['innovation'] = reference - data['estimate']
    
    return data
    

def covariance(simulation, measurements):    
    
    return 0
    
    
def bias(simulation, measurements):    
    
    return 0
