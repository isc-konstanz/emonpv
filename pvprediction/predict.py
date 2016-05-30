# -*- coding: utf-8 -*-
"""
    pvprediction.predict
    ~~~~~
    
    This module provides functions to predict photovoltaic generation and yield
    data, based on passed :class:`pvprediction.System` and :class:`pvprediction.Weather`
    objects, containing specific system orientation and location data, as well as 
    solar irradiation and temperature data.
    
"""
import logging
logger = logging.getLogger('pvprediction.predict')

import numpy as np
import pandas as pd


def energy(systems, weather):
    """ 
    Determines the energy yield of a dict of configured photovoltaic system 
    installations, given by solar irradiation and temperature data.
    The returned pandas DataFrame contains columns for each system, indicated
    by its id, as well as all systems sum.
    
    
    :param systems: 
        the dictionary of photovoltaic systems, the yield should be calculated for.
        Listed System objects are indexed by their specified system id.
    :type systems: 
        dict of :class:`pvprediction.System`
    
    :param weather:
        the solar irradiance data on a horizontal surface in W/m^2 
        and local temperature in degree Celsius.
    :type weather: 
        :class:`pvprediction.Weather`
    
    
    :returns: 
        the systems total calculated hourly energy yield, as well as the
        separate single systems' yield.
    :rtype: 
        :class:`pandas.DataFrame`
    """
    generation = power(systems, weather)
    
    energy = pd.DataFrame(data=np.nan, index=generation.index, columns=list(generation.columns))
    
    energy.iloc[0] = generation.iloc[0]
    for i in range(1, len(generation.index)):
        energy.iloc[i] = generation.iloc[i] + energy.iloc[i-1]
    
    # When more than one systems generation is calculated, a total generation column will
    # be present and will be renamed
    if 'generation' in energy.columns:
        energy.rename(columns={'generation':'yield'}, inplace=True)
        
    return energy
    

def power(systems, weather):
    """
    Determines the net output power of a dict of configured photovoltaic system 
    installations, given by solar irradiation and temperature data.
    The returned pandas DataFrame contains columns for each system, indicated
    by its id, as well as all systems sum.
    
    
    :param systems: 
        the dictionary of photovoltaic systems, the generation should be calculated for.
        Listed System objects are indexed by their specified system id.
    :type systems: 
        dict of :class:`pvprediction.System`
    
    :param weather:
        the solar irradiance data on a horizontal surface in W/m^2 
        and local temperature in degree Celsius.
    :type weather: 
        :class:`pvprediction.Weather`
    
    
    :returns: 
        the systems total calculated hourly generated power, as well as the
        separate single systems' generation.
    :rtype: 
        :class:`pandas.DataFrame`
    """
    
    systemids = []
    if (len(systems.keys()) > 1):
        systemids.append('generation')
    
    for sysid in systems.keys():
        systemids.append(sysid.lower())
    
    generation = pd.DataFrame(np.nan, weather.index, columns=systemids)
    for sysid, sys in systems.items():
        irradiation = weather.calculate(sys)
        
        if (len(systems.keys()) > 1):
            generation[sysid] = power_system(sys, irradiation, weather.temperature)
            generation['generation'] = generation[systemids[1:]].sum(axis=1)
        else:
            generation[sysid] = power_system(sys, irradiation, weather.temperature)
        
    return generation


def power_system(system, irradiation, temperature):
    """
    Determines the net output power of one specified photovoltaic system 
    installation, given by solar irradiation and local temperature data, 
    including various loss schemes.
    
    
    :param system: 
        the photovoltaic system, the yield should be calculated for.
    :type system: 
        :class:`pvprediction.System`
    
    :param irradiation:
        the solar irradiance data on a horizontal surface in W/m^2.
    :type irradiation:
        :class:`pandas.Series`
    
    :param temperature:
        the local temperature in degree Celsius.
    :type temperature:
        :class:`pandas.Series`
    
    
    :returns: 
        the systems' hourly generated average power.
    :rtype: 
        :class:`pandas.Series`
    """
    
    # The systems efficiency eta is an array with a value for each hour of the day,
    # with the index indicating the hour, and needs to be arranged to corresponding
    # timestamps
    eta = pd.Series(np.nan, index=irradiation.index, name='eta')
    for i in eta.index:
        eta.ix[i] = system.system_param['eta'][i.tz_convert('UTC').hour]
    
    power = power_effective(system, irradiation, temperature)
    power_sys = power*eta*system.modules_param['n']
    
    return power_sys
    

def power_effective(system, irradiation, temperature):
    """ 
    Calculates the effective output power of one specified photovoltaic 
    system installation, given by solar irradiation and local temperature data.
    
    
    :param system: 
        the photovoltaic system, the yield should be calculated for.
    :type system: 
        :class:`pvprediction.System`
    
    :param irradiation:
        the solar irradiance data on a horizontal surface in W/m^2.
    :type irradiation:
        :class:`pandas.Series`
    
    :param temperature:
        the local temperature in degree Celsius.
    :type temperature:
        :class:`pandas.Series`
    
    
    :returns: 
        the systems' hourly effective generated average power.
    :rtype: 
        :class:`pandas.Series`
    """
    logger.debug('Calculating pv generation for system "%s"', system.id)
    
    temp_module = temperature + (system.modules_param['noct'] - 20)/(0.8*system.system_param['irr_ref'])*irradiation
    
    power = system.modules_param['p_mpp']*irradiation/system.system_param['irr_ref']*(1 + system.modules_param['temp_coeff']/100*(temp_module - system.system_param['temp_ref']))
    power.name = 'power'
    
    return power


def optimize(system, transition, reference, forgetting=0.99):
    """ 
    Optimize the overall efficiency for each hour of the power prediction, 
    such as inverter or reflection losses, soiling, shading or degradation.
    Every hour will be separately optimized recursively, based on the error 
    of the prior estimation and reference.
    
    
    :param system: 
        the photovoltaic system, the hourly efficiency should be estimated for.
    :type system: 
        :class:`pvprediction.System`
    
    :param transition:
        the prior estimated effective power in W/m^2.
    :type transition:
        :class:`pandas.Series`
    
    :param reference:
        the reference value, to which the prediction error will be calculated 
        for in W/m^2.
    :type reference:
        :class:`pandas.Series`
    
    :param forgetting:
        the forgetting factor for the optimization. Smaller forgetting factors result
        in a smaller weight of past values and result in more flexible results.
    :type forgetting:
        float
    
    
    :returns: 
        the array of calculated efficiency estimations, indexed by its 
        corresponding UTC hour.
    :rtype: 
        :class:`numpy.array`
    """
    logger.debug('Starting efficiency parameter optimization for system "%s"', system.id)
    
    eta = system.system_param['eta']
    cov = system.system_param['cov']
    
    for i in reference.index:
        # Stored efficiency and covariance values are indexed by their according 
        # UTC hour of the day
        hour = i.tz_convert('UTC').hour
        z = reference.loc[i]
        
        if not np.isnan(z):
            if z > 0:
                h = float(transition.loc[i])
                x_prior = eta[hour]
                p_prior = cov[hour]
                if p_prior == 0.0:
                    p_prior = system.system_param['sigma']**2
                
                # Calculate Kalman gain, taking a forgetting factor into account, to 
                # enable the optimization to react to more recent environmental trends
                k = p_prior*h/(forgetting + h*p_prior*h)
                
                # Calculate the certainty for the new estimate
                p = (1. - k*h)*p_prior/forgetting
                
                # Avoid covariance convergance to zero, as this would stop the optimization
                # due to absolute certainty
                if p > 0:
                    cov[hour] = p
                    
                    x = x_prior + k*(z - h*x_prior)
                    if x > 1:
                        x = 1
                    eta[hour] = x
                
                else:
                    cov[hour] = p_prior
                    eta[hour] = x_prior
                
        else: logger.warn('Unable to find valid measurement to optimize '
                          'efficiency for hour %d of system "%s"', hour, system.id)
    
    system.system_param['eta'] = eta
    system.system_param['cov'] = cov
    system.save_parameters()
    
    return eta


def optimise_static(system, transition, reference):
    """ 
    Optimize the overall efficiency for each hour of the power prediction, 
    such as inverter or reflection losses, soiling, shading or degradation.
    Every hour will be optimized statically with cvxopt, based on the error 
    of the prior estimation and reference.
    
    
    :param system: 
        the photovoltaic system, the hourly efficiency should be estimated for.
    :type system: 
        :class:`pvprediction.System`
    
    :param transition:
        the estimated effective power for several prior days in W/m^2.
    :type transition: 
        :class:`pandas.DataFrame`
    
    :param reference:
        the reference values for several prior days, to which the prediction 
        error will be calculated for in W/m^2.
    :type reference: 
        :class:`pandas.DataFrame`
    
    
    :returns: 
        the array of calculated efficiency estimations, indexed by its 
        corresponding UTC hour.
    :rtype: 
        :class:`numpy.array`
    """
    import cvxopt as opt
    
    eta = system.system_param['eta']

    # Get multi index of non-empty rows
    index = np.flatnonzero((reference + transition).sum(axis=1))
    
    eff = np.zeros(index.size)
    for i in range(0, index.size):
        eff[i] = eta[index[i]]
    
    ref = np.matrix(reference.ix[index].mean(axis=1)).T
    trans = np.diag(transition.ix[index].mean(axis=1))
    
    
    # Solve the quadratic problem
    #
    # minimize    (1/2)*x'*Q*x + q'*x 
    # subject to  G*x <= h
    Q = 2*opt.matrix(trans.T*trans, tc='d')
    p = -2*opt.matrix(ref.T*trans, tc='d').T
    
    # Define optimization bounds
    # 0 <= eta <= 1
    G = opt.matrix(np.vstack([-np.eye(len(index)), 
                              np.eye(len(index))]))
    h = opt.matrix(np.vstack([np.zeros((len(index), 1)), 
                              np.ones((len(index), 1))]))
    
    # Chose last estimated efficiency as initial values
    init = {}
    init['x'] = opt.matrix(eff, tc='d')
    result = opt.solvers.qp(Q, p, G, h, initvals=init)
    
    for i in range(0, index.size):
        eta[index[i]] = result['x'][i]
    system.system_param['eta'] = eta
    system.save_parameters()

    return eta
