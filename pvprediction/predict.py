#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import os
import numpy as np
import pandas as pd

import systems
import optimize as opt

from configparser import ConfigParser


def energy(forecast, optimize):
    """ 
        Calculates the energy yield of a list of configured photovoltaic system installations, 
        given by a solar irradiation forecast.
    
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :returns: The systems energy yield.
        
    """
    prediction = power(forecast, optimize)
    
    yieldprediction = pd.DataFrame(data=np.nan, index=forecast.times, columns=list(prediction.columns))
    i = 0
    for t, row in yieldprediction.iterrows():
        if (i == 0):
            yieldprediction.ix[i] = prediction.ix[i]
        else:
            yieldprediction.ix[i] = prediction.ix[i] + yieldprediction.ix[i-1]
        i+=1
    
    return yieldprediction.rename(columns = {'generation':'yield'})
    

def power(forecast, optimize):
    """ 
        Calculates the net output power of a list of configured photovoltaic system installations, 
        given by a solar irradiation forecast.
    
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :param optimize: Boolean value, if parameters should be optimized before predicting irradiation.
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
            
    generation = pd.DataFrame(np.nan, forecast.times, columns=systemids)
    for id, sys in systemlist.items():
        if optimize:
            opt.efficiency(sys, forecast)
        
        if (len(systemlist.keys()) > 1):
            generation[id.lower()] = power_system(sys, forecast)
            generation['generation'] = generation[systemids[1:]].sum(axis=1)
        else:
            generation['generation'] = power_system(sys, forecast)
        
    return generation


def power_system(system, forecast):
    eta = system.get_eta(forecast.times)
    
    power = power_effective(system, forecast)
    power_sys = power*eta*system.modules_param['n']
    
    return power_sys    
    

def power_effective(system, forecast):
    """ 
        Calculates the net output power of one specified photovoltaic system installation, 
        given by a solar irradiation forecast, including various loss schemes.
    
        :param system: The installed photovoltaic system, whose generation should be calculated.
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :returns: The systems generated power.
        
    """
    irradiation = forecast.irradiation(system)
    
    # Convert the ambient temperature from Kelvin to Celsius and calculate the module temperature
    temp_ambient = forecast.temperature - 273.15
    temp_module = temp_ambient + (system.modules_param['noct'] - 20)/(0.8*system.system_param['irr_ref'])*irradiation
    
    power = system.modules_param['p_mpp']*irradiation/system.system_param['irr_ref']*(1 + system.modules_param['temp_coeff']/100*(temp_module - system.system_param['temp_ref']))
    
    return pd.Series(power, forecast.times, name='power')

