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
            
    
    def feed(self, name, start, end, datapoints):
        id = requests.get(self.url + 'feed/getid.json?', params={'apikey': self.apikey, 'name': name})
        
        params = {'apikey': self.apikey, 
                  'id': id.text.replace('"', ''), 
                  'start': start, 
                  'end': end, 
                  'dp': datapoints}
        
        resp = requests.get(self.url + 'feed/data.json?', params=params)
        
        datastr = resp.text
        datalist = eval(datastr)
        data = np.array(datalist)
        
        return pd.Series(data=data[:,1], index=data[:,0], name=name)
    
