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


def energy(forecast):
    """ 
        Calculates the energy yield of a list of configured photovoltaic system installations, 
        given by a solar irradiation forecast.
    
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :returns: The systems energy yield.
        
    """
    prediction = power(forecast)
    
    yieldprediction = pd.DataFrame(data=np.nan, index=forecast.index, columns=list(prediction.columns))
    i = 0
    for t, row in yieldprediction.iterrows():
        if (i == 0):
            yieldprediction.ix[i] = prediction.ix[i]
        else:
            yieldprediction.ix[i] = prediction.ix[i] + yieldprediction.ix[i-1]
        i+=1
    
    return yieldprediction.rename(columns = {'generation':'yield'})
    

def power(forecast):
    """ 
        Calculates the net output power of a list of configured photovoltaic system installations, 
        given by a solar irradiation forecast.
    
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :returns: The systems generated power.
        
    """
    here = os.path.abspath(os.path.dirname(__file__))
    settingsfile = os.path.join(os.path.dirname(here), 'conf', 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    systemlist = systems.read(float(settings.get('Location','latitude')), 
                              float(settings.get('Location','longitude')), 
                              float(settings.get('Location','altitude')),
                              str(settings.get('Location','timezone')))
    systemids = ['generation']
    if (len(systemlist.keys()) > 1):
        for id in systemlist.keys():
            systemids.append(id.lower())
    generation = pd.DataFrame(np.nan, forecast.index, columns=systemids)
    
    for id, sys in systemlist.items():
        generation[id.lower()] = systempower(sys, forecast)
    
    if (len(systemlist.keys()) > 1):
        generation['generation'] = generation[systemids[1:]].sum(axis=1)
        
    return generation


def systempower(system, forecast):
    """ 
        Calculates the net output power of one specified photovoltaic system installation, 
        given by a solar irradiation forecast, including various loss schemes.
    
        :param system: The installed photovoltaic system, whose generation should be calculated.
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :returns: The systems generated power.
        
    """
    irr_forecast = forecast.ix[:,:'direct']
    irradiation = system.irradiation(irr_forecast)
    
    # Convert the ambient temperature from Kelvin to Celsius and calculate the module temperature
    temp_ambient = forecast['temperature'] - 273.15
    temp_module = temp_ambient + (system.modules_param['noct'] - 20)/(0.8*system.system_param['irr_ref'])*irradiation
    
    p = system.modules_param['p_mpp']*irradiation/system.system_param['irr_ref']*(1 + system.modules_param['temp_coeff']/100*(temp_module - system.system_param['temp_ref']))
    p_sys = p*system.modules_param['n']*system.system_param['eta']
        
#     u_mpp = abs(system.modules_param['u_mpp0']*np.log(irradiation)/np.log(system.system_param['irr_ref'])).replace(np.inf, 0)
#     i_mpp = abs(system.modules_param['i_mpp0']*irradiation/system.system_param['irr_ref']).replace(np.inf, 0)
#     
#     # Convert the ambient temperature from Kelvin to Celsius and calculate the module temperature
#     temp_ambient = forecast['temperature'] - 273.15
#     temp_module = temp_ambient + irradiation*system.system_param['heatup_coeff']
#     
#     #module_area = system.modules_param['width']*system.modules_param['height']
#     p_mpp = u_mpp*i_mpp*(1 + system.modules_param['temp_coeff']/100*(temp_module - system.system_param['temp_ref']))
#     p_sys = p_mpp*system.modules_param['rows']*system.modules_param['nrow']*system.system_param['eta']
    
    return pd.Series(p_sys, forecast.index, name='power')

