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

from configparser import ConfigParser


def energy(forecast, optimize):
    """ 
        Calculates the energy yield of a list of configured photovoltaic system installations, 
        given by a solar irradiation forecast.
    
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :returns: The systems energy yield.
        
    """
    generation = power(forecast, optimize)
    
    energy = pd.DataFrame(data=np.nan, index=forecast.times, columns=list(generation.columns))
    i = 0
    for t, row in energy.iterrows():
        if (i == 0):
            energy.ix[i] = generation.ix[i]
        else:
            energy.ix[i] = generation.ix[i] + energy.ix[i-1]
        i+=1
    
    return energy.rename(columns = {'generation':'yield'})
    

def power(irradiation, optimize):
    """ 
        Calculates the net output power of a list of configured photovoltaic system installations, 
        given by a solar irradiation.
    
        :param irradiation: The solar irradiation on a horizontal surface.
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
    
    systemids = []
    if (len(systemlist.keys()) > 1):
        systemids.append('generation')
    
    for id in systemlist.keys():
        systemids.append(id.lower())
            
    generation = pd.DataFrame(np.nan, irradiation.times, columns=systemids)
    for id, sys in systemlist.items():
        if optimize:
            optimize(sys, irradiation)
        
        if (len(systemlist.keys()) > 1):
            generation[id] = power_system(sys, irradiation)
            generation['generation'] = generation[systemids[1:]].sum(axis=1)
        else:
            generation[id] = power_system(sys, irradiation)
        
    return generation


def power_system(system, irradiation):
    eta = pd.Series(np.nan, index=irradiation.times, name='eta')
    for i in eta.index:
        eta.ix[i] = system.system_param['eta'][i.tz_convert('UTC').hour]
    
    power = power_effective(system, irradiation)
    power_sys = power*eta*system.modules_param['n']
    
    return power_sys
    

def power_effective(system, irradiation):
    """ 
        Calculates the net output power of one specified photovoltaic system installation, 
        given by a solar irradiation, including various loss schemes.
    
        :param system: The installed photovoltaic system, whose generation should be calculated.
        :param irradiation: The solar irradiation on a horizontal surface.
        :returns: The systems generated power.
        
    """
    irr = irradiation.calculate(system)
    
    # Convert the ambient temperature from Kelvin to Celsius and calculate the module temperature
    temp_ambient = irradiation.temperature - 273.15
    temp_module = temp_ambient + (system.modules_param['noct'] - 20)/(0.8*system.system_param['irr_ref'])*irr
    
    power = system.modules_param['p_mpp']*irr/system.system_param['irr_ref']*(1 + system.modules_param['temp_coeff']/100*(temp_module - system.system_param['temp_ref']))
    
    return pd.Series(power, irradiation.times, name='power')


def optimize(system, irradiation, measurement, forgetting=0.99):
    eta = system.system_param['eta']
    cov = system.system_param['cov']
    
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
    
    system.system_param['eta'] = eta
    system.system_param['cov'] = cov
    system.save_parameters()
    
    return eta
    