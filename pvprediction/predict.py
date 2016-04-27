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
    eta = pd.Series(np.nan, index=forecast.times, name='eta')
    for i in eta.index:
        eta.ix[i] = system.system_param['eta'][i.tz_convert('UTC').hour]
    
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


def optimize(system, irradiation, measurement, forgetting=0.99):
    eta = [1]*24
    cov = [0]*24
    
    transition = power_effective(system, irradiation)*system.modules_param['n']
    
    for i in irradiation.times.tz_convert('UTC').hour:
        z = measurement.ix[i]
        
        if not np.isnan(z) and z > 0:
            h = float(transition[i])
            x_prior = system.system_param['eta'][i]
            p_prior = system.system_param['cov'][i]
            if p_prior == 0.0:
                p_prior = system.system_param['sigma']**2
            
            k = p_prior*h/(forgetting + h*p_prior*h)
            p = (1. - k*h)*p_prior/forgetting
            if p > 0:
                cov[i] = p
                
                x = x_prior + k*(z - h*x_prior)
                if x > 1:
                    x = 1
                eta[i] = x
            
            else:
                cov[i] = p_prior
                eta[i] = x_prior
            
        elif z > 0:
            cov[i] = system.system_param['cov'][i]
            eta[i] = system.system_param['eta'][i]
    
    system.system_param['eta'] = eta
    system.system_param['cov'] = cov
    system.save_parameters()
    
    