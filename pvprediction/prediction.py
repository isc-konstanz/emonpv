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

from pvprediction.systems import get_systems


def get_yield_prediction(forecast):
    """ 
        Calculates the energy yield of a list of configured photovoltaic system installations, 
        given by a solar irradiation forecast.
    
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :returns: The systems energy yield.
        
    """
    prediction = get_power_prediction(forecast)
    
    yieldprediction = pd.DataFrame(data=np.nan, index=forecast.index, columns=list(prediction.columns))
    i = 0
    for t, row in yieldprediction.iterrows():
        if (i == 0):
            yieldprediction.ix[i] = prediction.ix[i]
        else:
            yieldprediction.ix[i] = prediction.ix[i] + yieldprediction.ix[i-1]
        i+=1
    
    return yieldprediction.rename(columns = {'generation':'yield'})
    

def get_power_prediction(forecast):
    """ 
        Calculates the net output power of a list of configured photovoltaic system installations, 
        given by a solar irradiation forecast.
    
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :returns: The systems generated power.
        
    """
    here = os.path.abspath(os.path.dirname(__file__))
    settings = os.path.join(os.path.dirname(here), 'conf', 'settings.cfg')
    config = ConfigParser()
    config.read(settings)
    
    forecast.index.tz_localize('UTC').tz_convert(config.get('Location','timezone'))
    systems = get_systems(config.get('Location','latitude'), 
                          config.get('Location','longitude'), 
                          config.get('Location','timezone'))
    systemids = ['generation']
    if (len(systems.keys()) > 1):
        for id in systems.keys():
            systemids.append(id.lower())
    generation = pd.DataFrame(np.nan, forecast.index, columns=systemids)
    
    for id, system in systems.items():
        generation[id.lower()] = get_prediction(system, forecast)
    
    if (len(systems.keys()) > 1):
        generation['generation'] = generation[systemids[1:]].sum(axis=1)
        
    return generation


def get_prediction(system, forecast):
    """ 
        Calculates the net output power of one specified photovoltaic system installation, 
        given by a solar irradiation forecast, including various loss schemes.
    
        :param system: The installed photovoltaic system, whose generation should be calculated.
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :returns: The systems generated power.
        
    """
    irr_forecast = forecast.ix[:,:'direct']
    irradiance = system.get_tilted_irradiance(irr_forecast)
    
    
    u_mpp = (system.modules_param['u_mpp0']*np.log(irradiance['global'])/np.log(system.system_param['irr_ref'])).replace([np.inf, -np.inf], 0)
    i_mpp = (system.modules_param['i_mpp0']*irradiance['global']/system.system_param['irr_ref']).replace([np.inf, -np.inf], 0)

    # Convert the ambient temperature from Kelvin to Celsius and calculate the module temperature
    temp_ambient = forecast['temperature'] - 273.15
    temp_module = temp_ambient + irradiance['global']*system.system_param['heatup_coeff']    
    
    #module_area = system.modules_param['width']*system.modules_param['height']
    p_mpp = u_mpp*i_mpp*(1 + system.modules_param['temp_coeff']*(temp_module - system.system_param['temp_ref']))
    p_sys = p_mpp*system.modules_param['rows']*system.modules_param['nrow']*system.system_param['eta']
    
    return pd.DataFrame(p_sys, forecast.index, columns=['power'])
