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


def energy(forecast):
    """ 
        Calculates the energy yield of a list of configured photovoltaic system installations, 
        given by a solar irradiation forecast.
    
        :param forecast: The solar irradiance forecast on a horizontal surface.
        :returns: The systems energy yield.
        
    """
    generation = power(forecast)
    
    energy = pd.DataFrame(data=np.nan, index=forecast.times, columns=list(generation.columns))
    i = 0
    for t, row in energy.iterrows():
        if (i == 0):
            energy.ix[i] = generation.ix[i]
        else:
            energy.ix[i] = generation.ix[i] + energy.ix[i-1]
        i+=1
    
    return energy.rename(columns = {'generation':'yield'})
    

def power(irradiation, temperature):
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
    
    for sysid in systemlist.keys():
        systemids.append(sysid.lower())
    
    generation = pd.DataFrame(np.nan, irradiation.index, columns=systemids)
    for sysid, sys in systemlist.items():
        if (len(systemlist.keys()) > 1):
            generation[sysid] = power_system(sys, irradiation, temperature)
            generation['generation'] = generation[systemids[1:]].sum(axis=1)
        else:
            generation[sysid] = power_system(sys, irradiation, temperature)
        
    return generation


def power_system(system, irradiation, temperature):
    eta = pd.Series(np.nan, index=irradiation.index, name='eta')
    for i in eta.index:
        eta.ix[i] = system.system_param['eta'][i.tz_convert('UTC').hour]
    
    power = power_effective(system, irradiation, temperature)
    power_sys = power*eta*system.modules_param['n']
    
    return power_sys
    

def power_effective(system, irradiation, temperature):
    """ 
        Calculates the net output power of one specified photovoltaic system installation, 
        given by a solar irradiation, including various loss schemes.
    
        :param system: The installed photovoltaic system, whose generation should be calculated.
        :param irradiation: The solar irradiation on a horizontal surface.
        :returns: The systems generated power.
        
    """
    
    temp_module = temperature + (system.modules_param['noct'] - 20)/(0.8*system.system_param['irr_ref'])*irradiation
    
    power = system.modules_param['p_mpp']*irradiation/system.system_param['irr_ref']*(1 + system.modules_param['temp_coeff']/100*(temp_module - system.system_param['temp_ref']))
    power.name = 'power'
    
    return power


def optimize(system, transition, reference, eta, cov, forgetting=0.99):
    for i in reference.index:
        hour = i.tz_convert('UTC').hour
        z = reference.loc[i]
        
        if not np.isnan(z) and z > 0:
            h = float(transition.loc[i])
            x_prior = system.system_param['eta'][hour]
            p_prior = system.system_param['cov'][hour]
            if p_prior == 0.0:
                p_prior = system.system_param['sigma']**2
            
            k = p_prior*h/(forgetting + h*p_prior*h)
            p = (1. - k*h)*p_prior/forgetting
            if p > 0:
                cov[hour] = p
                
                x = x_prior + k*(z - h*x_prior)
                if x > 1:
                    x = 1
                eta[hour] = x
            
            else:
                cov[hour] = p_prior
                eta[hour] = x_prior
    
    system.system_param['eta'] = eta
    system.system_param['cov'] = cov
    system.save_parameters()
    
    return eta
    