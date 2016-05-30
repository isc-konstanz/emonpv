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
    here = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    method_ref = 'forecast'
    method_opt = 'static'
    
    configdir = os.path.join(os.path.dirname(here), 'conf')
    
    settingsfile = os.path.join(configdir, 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    weatherdir = str(settings.get('General','datadir'))
    if not os.path.exists(weatherdir):
        logger.error('The specified directory "%s" does not exist', weatherdir)
        quit()
        
    simdir = os.path.join(str(settings.get('General','datadir')), 'sim')
    if not os.path.exists(simdir):
        os.makedirs(simdir)
    
    emoncms = Emoncms(settings.get("Emoncms","URL"), settings.get("Emoncms","APIkey"))
    
    systems = pv.system.read(configdir)
    
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
                
                if not measurements.empty and (measurements > 0).any() and not measurements.isnull().any() and measurements.index.equals(times):
                    if not method_opt:
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
                    
                    
                    
                    filename = forecast.key + '_opt_' + sysid + '.csv';
                    filepath = os.path.join(simdir, filename)
                    
                    est = pv.predict.power_effective(sys, forecast.calculate(sys), forecast.temperature)*eta*sys.modules_param['n']
                    est.name = 'estimation'
                    
                    e_est = pd.Series(est - measurements, name='e_est')
                    e_rel_est = (e_est/measurements).replace(np.inf,0).replace(-np.inf,0).fillna(0)*100
                    
                    if method_ref == 'reference':
                        reference = dwd_meas[(dwd_meas.index >= forecast.index[0] - datetime.timedelta(minutes=30)) & 
                                             (dwd_meas.index <= forecast.index[-1] + datetime.timedelta(minutes=30))]
                        reference.key = sysid + '_dwd'
                         
                        ref = pv.predict.power_effective(sys, reference.calculate(sys), reference.temperature.dropna()).dropna()*eta*sys.modules_param['n']
                        ref.name = 'reference'
                        
                        e_ref = pd.Series(ref - measurements, name='e_ref')
                        e_rel_ref = (e_ref/measurements).replace(np.inf,0).replace(-np.inf,0).fillna(0)*100
                        
                        sim = pd.concat([measurements, est, ref, e_est, e_ref], axis=1)
                    
                    else:
                        sim = pd.concat([measurements, est, e_est], axis=1)
                        
                    sim.to_csv(filepath, sep=',', encoding='utf-8')
                    
                    
                    if not method_ref is None:
                        _concat_file(os.path.join(simdir, 'efficiency.csv'), eta, forecast.key)
                        
                    _concat_file(os.path.join(simdir, 'innovation.csv'), e_est, forecast.key)
                    _concat_file(os.path.join(simdir, 'error.csv'), e_rel_est, forecast.key)
                    
                    if method_ref == 'reference':
                        _concat_file(os.path.join(simdir, 'innovation_ref.csv'), e_ref, forecast.key)
                        _concat_file(os.path.join(simdir, 'error_ref.csv'), e_rel_ref, forecast.key)
                
                else:
                    logger.warn('Unable to find valid measurements for "%s"', times[0])
            
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
                              float(settings.get('Optimization','forgetting')))
    
    return eta


def _optimize_static(time, system, settings, weatherdir, measurements, transitions, references, reference=None, method=None):
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
    
    eta = pv.predict.optimise_static(system, transitions, references)
    
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
    if not series.isnull().any() and np.count_nonzero(series)/float(len(series)) > 0.3:
        if os.path.isfile(filename):
            csv = pd.read_csv(filename, index_col='hours', encoding='utf-8')
        else:
            csv = pd.DataFrame()
        series.name = key
        series.index = series.index.hour
        series.index.name = 'hours'
        
        csv = pd.concat([csv, series], axis=1).fillna(0)
        csv.to_csv(filename, sep=',', encoding='utf-8')


if __name__ == '__main__':
    main()