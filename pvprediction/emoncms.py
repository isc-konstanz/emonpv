# -*- coding: utf-8 -*-
"""
    pvprediction.emoncms
    ~~~~~
    
    This module implements a simple communication with an emoncms webserver.
    The Energy monitoring Content Management System is an open-source web-app for processing, 
    logging and visualising energy, temperature and other environmental data as part of the 
    OpenEnergyMonitor project.
    
"""
import logging
logger = logging.getLogger('pvprediction.emoncms')

import requests
import numpy as np
import pandas as pd


class Emoncms:
    """
    The Emoncms object implements basic inter-process communication 
    and enables the retrieving of logged emoncms v8.3.6 feed data 
    with :func:`feed`.
    
    It passes the emoncms servers' address and API key.
    
    
    :param url:
        the fully resolved URL of the emoncms server.
    :type url:
        str or unicode
        
    :param apikey: 
        the API key of the addressed emoncms user.
        May be either Read or Write key to retrieve data.
    :type apikey:
        str or unicode
    """
    
    def __init__(self, url, apikey):
        self.url = url
        self.apikey = apikey
            
    
    def feed(self, name, times, timezone):
        """
        Retrieves logged emoncms v8.3.6 feed data and returns
        both averaged values, as well all retrieved data points in detail.
        
        
        :param name:
            the full name of the feed to retrieve.
        :type name:
            str or unicode
        
        :param times:
            the index, determining the interval to be retrieved.
            Additionally, resulting data will reindexed and averaged to it.
        :type times:
            :class:`pandas.DatetimeIndex`
        
        :param timezone: 
            the timezone, to which the retrieved data will be converted to.
        :type timezone:
            str or unicode
        
        
        :returns: 
            the retrieved feed data, averaged by passed times parameter,
            and the detailed, retrieved feed data.
        :rtype: 
            :class:`pandas.Series`
        """
        logger.debug('Starting request for feed "%s"', name)
        feedid = requests.get(self.url + 'feed/getid.json?', params={'apikey': self.apikey, 'name': name})
        
        # Convert times to UTC UNIX timestamps
        timestamps = times.tz_convert('UTC').astype(np.int64)//10**6
        
        # Offset end timestamp by one hour for averaging purposes
        step = 59*60*1000
        start = timestamps[0]
        end = timestamps[-1] + step
        
        # At the moment fetch data in a 1 min interval in microseconds
        interval = 60*1000
        datapoints = int((end - start)/interval)
        
        params = {'apikey': self.apikey, 
                  'id': feedid.text.replace('"', ''), 
                  'start': start, 
                  'end': end, 
                  'dp': datapoints}
        
        resp = requests.get(self.url + 'feed/data.json?', params=params)
        
        datastr = resp.text
        dataarr = np.array(eval(datastr))
        data = pd.Series(data=dataarr[:,1], index=dataarr[:,0], name='data')
        
        logger.debug('Received %d values from feed "%s"',len(data), name)
        
        # The first and last values returned will be the nearest values to 
        # the specified timestamps and can be outside of the actual interval.
        # Those will be dropped to avoid additional index values when resampling
        data = data.ix[start:end]
        data.index = pd.to_datetime(data.index,unit='ms')
        data.index = data.index.tz_localize('UTC').tz_convert(timezone)
        data.index.name = 'time'
        
        avg = pd.Series(data.resample('1h').mean(), name='average')
        
        return avg

