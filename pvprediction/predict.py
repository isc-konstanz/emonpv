#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import logging
logger = logging.getLogger('pvprediction.predict')

import numpy as np
import pandas as pd


def energy(systems, weather):
    """ 
        Calculates the energy yield of a list of configured photovoltaic system installations, 
        given by a solar irradiation forecast.
    
        :param systems: The solar irradiance forecast on a horizontal surface.
        :param weather: This method does the same as :class:`Weather`
        :returns: The systems energy yield.
        
    """
    generation = power(systems, weather)
    
    energy = pd.DataFrame(data=np.nan, index=generation.index, columns=list(generation.columns))
    energy.rename(columns = {'generation':'yield'})
    
    energy.iloc[0] = generation.iloc[0]
    for i in range(1,energy.size):
        energy.iloc[i] = generation.iloc[i] + energy.iloc[i-1]
    
    return energy
    

def power(systems, weather):
    """ 
        Calculates the net output power of a list of configured photovoltaic system installations, 
        given by a solar irradiation.
    
        :param irradiation: The solar irradiation on a horizontal surface.
        :returns: The systems generated power.
        
    """
    if not systems:
        logger.warn('System list is empty')
    
    systemids = []
    if (len(systems.keys()) > 1):
        systemids.append('generation')
    
    for sysid in systems.keys():
        systemids.append(sysid.lower())
    
    generation = pd.DataFrame(np.nan, weather.index, columns=systemids)
    for sysid, sys in systems.items():
        logger.debug('Calculating pv generation for system "%s"', sysid)
        
        irradiation = weather.calculate(sys)
        
        if (len(systems.keys()) > 1):
            generation[sysid] = power_system(sys, irradiation, weather.temperature)
            generation['generation'] = generation[systemids[1:]].sum(axis=1)
        else:
            generation[sysid] = power_system(sys, irradiation, weather.temperature)
        
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
    