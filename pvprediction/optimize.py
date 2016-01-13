#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import logging
logger = logging.getLogger('pvprediction')

import os
import numpy as np
import pandas as pd
import cvxopt as opt

import tools
import predict
import forecast as fc
from emoncms import Emoncms

from configparser import ConfigParser


def efficiency(system, forecast):
    references, estimates = _get_historicdata(system, forecast)
        
    # Get multi index of non-empty rows
    hours = references.index
    index = hours[pd.concat([references, estimates], axis=1).sum(axis=1) > 0]
    
    ref = np.matrix(references.ix[index].sum(axis=1)).T
    est = np.diag(estimates.ix[index].sum(axis=1))
    
    
    # Solve the quadratic problem
    #
    # minimize    (1/2)*x'*Q*x + q'*x 
    # subject to  G*x <= h
    Q = 2*opt.matrix(est.T*est, tc='d')
    p = -2*opt.matrix(ref.T*est, tc='d').T
    
    # Define optimization bounds
    # 0 <= eta <= 1
    G = opt.matrix(np.vstack([-np.eye(len(index)), 
                              np.eye(len(index))]))
    h = opt.matrix(np.vstack([np.zeros((len(index), 1)), 
                              np.ones((len(index), 1))]))
    
    # Chose last estimated efficiency as initial values
    init = {}
    init['x'] = opt.matrix(system.get_eta(index), tc='d')
    result = opt.solvers.qp(Q, p, G, h, initvals=init)
    
    eta = pd.Series(result['x'], index=index, name='eta')
    eta = eta.reindex(hours, fill_value=0)
    system.save_eta(eta)
    
    estimates = estimates.multiply(eta, axis="index")
    error = references - estimates
    
    my = pd.Series(np.mean(error, axis=1), name='my')
    sigma = pd.Series(np.std(error, axis=1), name='sigma')

    return pd.concat([eta, error, my, sigma], axis=1)


def _get_historicdata(system, forecast):
    from pytz import AmbiguousTimeError

    here = os.path.abspath(os.path.dirname(__file__))
    settingsfile = os.path.join(os.path.dirname(here), 'conf', 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    emoncms = Emoncms(settings.get("Emoncms","URL"), settings.get("Emoncms","APIkey"))
    
    references = pd.DataFrame()
    estimates = pd.DataFrame()
    
    # Continue to read forecast files, until the defined number of valid references got read
    count = 0
    time = forecast.times[0]
    while count < int(settings.get('Optimization','days')):
        time = time - pd.DateOffset(days=1)
        file = fc.get_filename(time, settings.get("Location","key"))
        if not os.path.isfile(os.path.join(forecast.dir, file)):
            logger.warn('Unable to find forecast "%s". Optimization will be proceeded with %d days', file, count)
            break
        f = fc.read(os.path.join(forecast.dir, file), settings.get('Location','timezone'))
        
        try:
            ref, meas = emoncms.feed(system.id, f.times, system.location.tz)
            
            # Only use complete references for every hour, since cvxopt can't handle NaN values
            if not ref.empty and not ref.isnull().values.any() and ref.index.equals(f.times):
                ref.name = f.id
                ref.index = ref.index.tz_convert('UTC').hour
                references = pd.concat([references, ref], axis=1)
                
                est = predict.power_effective(system, f)*system.modules_param['n']
                est.name = f.id
                est.index = est.index.tz_convert('UTC').hour
                estimates = pd.concat([estimates, est], axis=1)
                
                count += 1
            else:
                logger.debug('Reference for forecast "%s" returned invalid', f.id)
        # AmbiguousTimeError will be thrown for some pandas version, if a daylight savings time crossing gets converted
        except AmbiguousTimeError, e:
            logger.warn('Error while retrieving reference for forecast "%s"', f.id)#, exc_info=True)
    
    if references.empty:
        raise ValueError('Optimization unable to retrieve references') 
    
    return references, estimates
