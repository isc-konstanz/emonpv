#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import os
import numpy as np
import pandas as pd
from configparser import ConfigParser
from emoncms import Emoncms
import predict
    
    
def parameters(system, forecast):
    reference, measurements = get_reference(system, forecast.index)
    estimate = predict.systempower(system, forecast)
    estimate.name = 'estimate'
    
    if not (measurements.empty):
        data = pd.concat([measurements, reference, estimate], axis=1)
        data['innovation'] = data['reference'] - data['estimate']
        
        return data
    else:
        return estimate
    
    
def get_reference(system, times):
    here = os.path.abspath(os.path.dirname(__file__))
    settingsfile = os.path.join(os.path.dirname(here), 'conf', 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    emoncms = Emoncms(settings.get("Emoncms","URL"), settings.get("Emoncms","APIkey"))
    
    # Bad style of hardcoded 3min feed interval. Needs to be redone
    timestamps = times.astype(np.int64)//10**6
    interval = 3*60*1000
    # Offset start and end by 3min, to compensate possible emoncms time offsets
    step = timestamps[1] -  timestamps[0]
    start = timestamps[0] - step
    end = timestamps[-1] + step
    datapoints = int((end - start)/interval)
    
    measurements = emoncms.feed(system.id.lower() + '_out_power', start, end, datapoints)
    measurements = measurements.ix[start:end]
    measurements.index = pd.to_datetime(measurements.index,unit='ms')
    measurements.index = measurements.index.tz_localize(settings.get('Location','timezone'))
    measurements.index.name = 'time'
    
    # Average measurements to get hourly reference values
    reference = pd.Series(np.nan, index=times, name='reference')
    for time in reference.index:
        start = time + pd.DateOffset(minutes=-30)
        end = time + pd.DateOffset(minutes=30)
        range = measurements.ix[start:end]
        reference.ix[time] = range.mean()
    
    return reference, measurements
    

def _innovation_covariance(simulation, measurements):    
    
    return 0


