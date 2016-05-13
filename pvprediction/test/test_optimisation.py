#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""    
    Optimizes the prediction parameters of a photovoltaic energy systems, according to solar irradiance forecasts
    
"""
import logging
logger = logging.getLogger('pvprediction')

import os
import datetime
from pytz import AmbiguousTimeError
from configparser import ConfigParser

import numpy as np
import pandas as pd
import pvprediction as pv
from pvprediction.emoncms import Emoncms


def main(args=None):
    method_ref = 'forecast'
    method_opt = 'static'
    here = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    configdir = os.path.join(os.path.dirname(here), 'conf')
    weatherdir = os.path.join(os.path.dirname(here), 'ref')
    
    settingsfile = os.path.join(configdir, 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    emoncms = Emoncms(settings.get("Emoncms","URL"), settings.get("Emoncms","APIkey"))
    
    systems = pv.systems.read(configdir,
                              float(settings.get('Location','latitude')), 
                              float(settings.get('Location','longitude')), 
                              float(settings.get('Location','altitude')),
                              str(settings.get('Location','timezone')))
    
    forecast = pv.weather.forecast(datetime.datetime.now(), 
                                   settings.get('Location','timezone'), 
                                   var=os.path.join(weatherdir, settings.get("DWD","key")), 
                                   method='DWD_CSV')
    
    if method_ref == 'reference':
        dwd_meas = pv.weather.reference(datetime.datetime.now(), 
                                        settings.get('Location','timezone'), 
                                        var=settings.get("DWD","id"), 
                                        method='DWD_PUB')
        
    if method_opt == 'static':
        transitions = pd.DataFrame()
        references = pd.DataFrame()
    
    reference = pd.DataFrame()
    measurements = pd.Series(np.nan, name='measurements')
    start = forecast.index[0]
    for i in range(-170, 1):
        time = start + datetime.timedelta(days=i)
        forecast = pv.weather.forecast(time, 
                                       settings.get('Location','timezone'), 
                                       var=os.path.join(weatherdir, settings.get("DWD","key")), 
                                       method='DWD_CSV')
        
        logger.info('Starting optimized prediction for forecast: %s', forecast.key)
        for sysid, sys in systems.items():
            times = forecast.index - datetime.timedelta(days=1)
            try:
                if method_ref == 'reference' and (reference.empty or not reference.index.equals(times)):
                    reference = dwd_meas[(dwd_meas.index >= times[0] - datetime.timedelta(minutes=30)) & 
                                         (dwd_meas.index <= times[-1] + datetime.timedelta(minutes=30))]
                    reference.key = sysid + '_dwd'
                
                if measurements.empty or not measurements.index.equals(times):
                    measurements, meas_detailed = emoncms.feed('device' + sys.id.lower() + '_out_power', times, settings.get('Location','timezone'))
                    measurements.name = 'measurements'
                
                if not measurements.empty and (measurements > 0).any() and measurements.index.equals(times):
                    if not method_ref:
                        result = sys.system_param['eta']
                        
                    elif method_opt == 'recursive':
                        result = _optimize_rec(times[0], sys, settings, weatherdir, 
                                               measurements, reference=reference, 
                                               method=method_ref)
                        
                    elif method_opt == 'static':
                        result, transitions, references = _optimize_static(times[0], sys, settings, weatherdir, 
                                                                           measurements, transitions, references, reference=reference, 
                                                                           method=method_ref)
                    
                    eta = pd.Series(np.nan, index=forecast.index, name='eta')
                    for i in eta.index:
                        eta.ix[i] = result[i.tz_convert('UTC').hour]
                    
                    measurements, meas_detailed = emoncms.feed('device' + sys.id.lower() + '_out_power', forecast.index, settings.get('Location','timezone'))
                    measurements.name = 'measurements'
                    
                    
                    
                    datadir = os.path.join(os.path.dirname(here), 'data')
                    filename = forecast.key + '_opt_' + sysid + '.csv';
                    filepath = os.path.join(datadir, filename)
                    
                    est = pv.predict.power_effective(sys, forecast.calculate(sys), forecast.temperature)*eta*sys.modules_param['n']
                    est.name = 'estimation'
                    
                    error_est = pd.Series(measurements - est, name='e_est')
                    
                    if method_ref == 'reference':
                        reference = dwd_meas[(dwd_meas.index >= forecast.index[0] - datetime.timedelta(minutes=30)) & 
                                             (dwd_meas.index <= forecast.index[-1] + datetime.timedelta(minutes=30))]
                        reference.key = sysid + '_dwd'
                         
                        ref = pv.predict.power_effective(sys, reference.calculate(sys), reference.temperature.dropna()).dropna()*eta*sys.modules_param['n']
                        ref.name = 'reference'
                        
                        error_ref = pd.Series(measurements - ref, name='e_ref')
                        
                        sim = pd.concat([measurements, est, ref, error_est, error_ref], axis=1)
                    
                    else:
                        sim = pd.concat([measurements, est, error_est], axis=1)
                        
                    sim.to_csv(filepath, sep=',', encoding='utf-8')
                    
                    
                    if method_ref:
                        _concat_file(os.path.join(datadir, 'efficiency.csv'), eta, forecast.key)
                        
                    _concat_file(os.path.join(datadir, 'innovation.csv'), error_est, forecast.key)
                    
                    if method_ref == 'reference':
                        _concat_file(os.path.join(datadir, 'innovation_ref.csv'), error_ref, forecast.key)
                    
            except AmbiguousTimeError:
                # AmbiguousTimeError will be thrown for some pandas version, if a daylight savings time crossing gets converted
                logger.warn('Error retrieving measurement data due to daylight savings timestamps for forecast: %s', forecast.key)


def _optimize_rec(time, system, settings, weatherdir, measurements, reference=None, method=None):
    power_eff = None
    if method == 'forecast':
        forecast_prior = _parse_forecasts(time, os.path.join(weatherdir, settings.get("DWD","key")), settings.get('Location','timezone'))
        power_eff = pv.predict.power_effective(system, forecast_prior.calculate(system), forecast_prior.temperature)*system.modules_param['n']
    
    elif method == 'reference':
        power_eff = pv.predict.power_effective(system, reference.calculate(system), reference.temperature.dropna()).dropna()*system.modules_param['n']
    
    eta = pv.predict.optimize(system, power_eff, measurements, 
                              system.system_param['eta'], system.system_param['cov'], 
                              float(settings.get('Optimization','forgetting')))
    
    return eta


def _optimize_static(time, system, settings, weatherdir, measurements, transitions, references, reference=None, method=None):
    if not measurements.isnull().any():
        earliest = time - datetime.timedelta(days=int(settings.get('Optimization','days')))
        if not references.empty and references.columns[0] < earliest:
            references = references.drop(references.columns[0], axis=1)
        
        meas = measurements.copy()
        meas.name = meas.index[0]
        meas.index = meas.index.hour
        references = pd.concat([references, meas], axis=1)
        
        power_eff = None
        if method == 'forecast':
            forecast_prior = _parse_forecasts(time, os.path.join(weatherdir, settings.get("DWD","key")), settings.get('Location','timezone'))
            power_eff = pv.predict.power_effective(system, forecast_prior.calculate(system), forecast_prior.temperature)*system.modules_param['n']
        
        elif method == 'reference':
            power_eff = pv.predict.power_effective(system, reference.calculate(system), reference.temperature.dropna()).dropna()*system.modules_param['n']
        
        power_eff.name = power_eff.index[0]
        power_eff.index = power_eff.index.hour
        transitions = pd.concat([transitions, power_eff], axis=1)
        
        eta = pv.predict.optimise_static(system, transitions, references, system.system_param['eta'])
    
    else:
        eta = system.system_param['eta']
        logger.warn('Unable to find valid measurements for "%s". Optimization will be skipped', time)
    
    return eta, transitions, references


def _parse_forecasts(time, path, timezone):
    forecast = pv.weather.forecast(time, timezone, var=path, method='DWD_CSV')
    result = forecast[0:6]
    
    for i in range(1,4):
        t = time + datetime.timedelta(hours=6*i)
        f = pv.weather.forecast(t, timezone, var=path, method='DWD_CSV')
        if f[0:6].isnull().any(axis=1).any():
            f = forecast[0:6]
        
        result = pd.concat([result, f[0:6]], axis=0)
    
    return result


def _concat_file(filename, series, key):
    if os.path.isfile(filename):
        csv = pd.read_csv(filename, index_col='hours', encoding='utf-8')
    else:
        csv = pd.DataFrame()
    series.name = key
    series.index = series.index.hour
    series.index.name = 'hours'
    
    csv = pd.concat([csv, series], axis=1)
    csv.to_csv(filename, sep=',', encoding='utf-8')


if __name__ == '__main__':
    main()