#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import requests
import numpy as np
import pandas as pd


class Emoncms:
    """ 
        Emoncms (Energy monitoring Content Management System) is an open-source web-app for processing, 
        logging and visualising energy, temperature and other environmental data as part of the 
        OpenEnergyMonitor project.
        
        This class enables the retrieving of logged emoncms v8.3.6 feed data.
        
    """
    
    def __init__(self, url, apikey):
        self.url = url
        self.apikey = apikey
            
    
    def feed(self, name, times, timezone):
        id = requests.get(self.url + 'feed/getid.json?', params={'apikey': self.apikey, 'name': name})
        
        # Offset end timestamp by one hour for averaging purposes
        timestamps = times.tz_convert('UTC').astype(np.int64)//10**6
        step = 59*60*1000
        start = timestamps[0]
        end = timestamps[-1] + step
        
        # Bad style of hardcoded 3min feed interval. Needs to be redone
        interval = 3*60*1000
        datapoints = int((end - start)/interval)
        
        params = {'apikey': self.apikey, 
                  'id': id.text.replace('"', ''), 
                  'start': start, 
                  'end': end, 
                  'dp': datapoints}
        
        resp = requests.get(self.url + 'feed/data.json?', params=params)
        
        datastr = resp.text
        dataarr = np.array(eval(datastr))
        data = pd.Series(data=dataarr[:,1], index=dataarr[:,0], name='data')
        
        data = data.ix[start:end]
        data.index = pd.to_datetime(data.index,unit='ms')
        data.index = data.index.tz_localize('UTC').tz_convert(timezone)
        data.index.name = 'time'
        
        hourly = pd.Series(data.resample('1h', how='mean'), name='hourly')
        
        return hourly, data
    
