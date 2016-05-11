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
    here = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    configdir = os.path.join(os.path.dirname(here), 'conf')
    referencedir = os.path.join(os.path.dirname(here), 'ref')
    
    settingsfile = os.path.join(configdir, 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    emoncms = Emoncms(settings.get("Emoncms","URL"), settings.get("Emoncms","APIkey"))
    
    systems = pv.systems.read(configdir,
                              float(settings.get('Location','latitude')), 
                              float(settings.get('Location','longitude')), 
                              float(settings.get('Location','altitude')),
                              settings.get('Location','timezone'))
    
    forecast = pv.weather.forecast(datetime.datetime.now(), 
                                   settings.get('Location','timezone'), 
                                   var=os.path.join(referencedir, settings.get("DWD","key")), 
                                   method='DWD_CSV')
    
    dwd_meas = pv.weather.reference(datetime.datetime.now(), 
                                    settings.get('Location','timezone'), 
                                    var=settings.get("DWD","id"), 
                                    method='DWD_PUB')
    
    reference = None
    measurements = pd.Series(np.nan, name='measurements')
    start = forecast.index[0]
    for i in range(-175, 1):
        time = start + datetime.timedelta(days=i)
        time = time.replace(hour=0)
        forecast = pv.weather.forecast(time, 
                                       settings.get('Location','timezone'), 
                                       var=os.path.join(referencedir, settings.get("DWD","key")), 
                                       method='DWD_CSV')
        
        logger.info('Starting optimized prediction for forecast: %s', forecast.key)
        for sysid, sys in systems.items():
            times = forecast.index - datetime.timedelta(days=1)
            try:
                if reference is None or not reference.index.equals(times):
                    reference = dwd_meas[(dwd_meas.index >= times[0] - datetime.timedelta(minutes=30)) & 
                                         (dwd_meas.index <= times[-1] + datetime.timedelta(minutes=30))]
                    reference.key = sysid + '_dwd'
                
                if measurements.empty or not measurements.index.equals(times):
                    measurements, meas_detailed = emoncms.feed('device' + sys.id.lower() + '_out_power', times, settings.get('Location','timezone'))
                    measurements.name = 'measurements'
                
                if not measurements.empty and (measurements > 0).any() and measurements.index.equals(times):
#                     result = sys.system_param['eta']
                    power_eff = pv.predict.power_effective(sys, reference.calculate(sys), reference.temperature.dropna()).dropna()*sys.modules_param['n']
#                     forecast_prior = pvprediction.weather.forecast(times[0], 
#                                                              settings.get('Location','timezone'), 
#                                                              var=os.path.join(referencedir, settings.get("DWD","key")), 
#                                                              method='DWD_CSV')
#                     power_eff = pv.predict.power_effective(sys, forecast_prior.calculate(sys), forecast_prior.temperature)*sys.modules_param['n']
#                     irr_forecast = pv.predict.power_effective(sys, forecast_prior.calculate(sys), forecast_prior.temperature)
#                     irr_ref = pv.predict.power_effective(sys, reference.calculate(sys), reference.temperature.dropna()).dropna()
#                     power_eff = pd.concat([irr_forecast, irr_forecast, irr_ref], axis=1).mean(axis=1)*sys.modules_param['n']
                    result = pv.predict.optimize(sys, power_eff, measurements, 
                                                 sys.system_param['eta'], sys.system_param['cov'], 
                                                 float(settings.get('Optimization','forgetting')))
                    
                    eta = pd.Series(np.nan, index=forecast.index, name='eta')
                    for i in eta.index:
                        eta.ix[i] = result[i.tz_convert('UTC').hour]
                    
                    measurements, meas_detailed = emoncms.feed('device' + sys.id.lower() + '_out_power', forecast.index, settings.get('Location','timezone'))
                    measurements.name = 'measurements'
                    
                    est = pv.predict.power_effective(sys, forecast.calculate(sys), forecast.temperature)*eta*sys.modules_param['n']
                    est.name = 'estimation'
                    
                    reference = dwd_meas[(dwd_meas.index >= forecast.index[0] - datetime.timedelta(minutes=30)) & 
                                         (dwd_meas.index <= forecast.index[-1] + datetime.timedelta(minutes=30))]
                    reference.key = sysid + '_dwd'
                     
                    ref = pv.predict.power_effective(sys, reference.calculate(sys), reference.temperature.dropna()).dropna()*eta*sys.modules_param['n']
                    ref.name = 'reference'
                    
                    datadir = os.path.join(os.path.dirname(here), 'data')
                    filename = forecast.key + '_opt_' + sysid + '.csv';
                    filepath = os.path.join(datadir, filename)
                    
                    error_est = pd.Series(measurements - est, name='e_est')
                    error_ref = pd.Series(measurements - ref, name='e_ref')
                    sim = pd.concat([measurements, est, ref, error_est, error_ref], axis=1)
#                     sim = pd.concat([measurements, est, error_est], axis=1)
                    sim.to_csv(filepath, sep=',', encoding='utf-8')
                    
                    
                    innovationfile = os.path.join(datadir, 'innovation.csv')
                    if os.path.isfile(innovationfile):
                        innovation = pd.read_csv(innovationfile, index_col='hours', encoding='utf-8')
                    else:
                        innovation = pd.DataFrame()
                    error_est.name = forecast.key
                    error_est.index = error_est.index.hour
                    error_est.index.name = 'hours'
                    innovation = pd.concat([innovation, error_est], axis=1)
                    innovation.to_csv(innovationfile, sep=',', encoding='utf-8')
                    
                    
                    innovationreffile = os.path.join(datadir, 'innovation_ref.csv')
                    if os.path.isfile(innovationreffile):
                        innovation = pd.read_csv(innovationreffile, index_col='hours', encoding='utf-8')
                    else:
                        innovation = pd.DataFrame()
                    error_ref.name = forecast.key
                    error_ref.index = error_ref.index.hour
                    error_ref.index.name = 'hours'
                    innovation = pd.concat([innovation, error_ref], axis=1)
                    innovation.to_csv(innovationreffile, sep=',', encoding='utf-8')
                    
                    
                    efficiencyfile = os.path.join(datadir, 'efficiency.csv')
                    if os.path.isfile(efficiencyfile):
                        efficiency = pd.read_csv(efficiencyfile, index_col='hours', encoding='utf-8')
                    else:
                        efficiency = pd.DataFrame()
                    eta.name = forecast.key
                    eta.index = eta.index.hour
                    eta.index.name = 'hours'
                    efficiency = pd.concat([efficiency, eta], axis=1)
                    efficiency.to_csv(efficiencyfile, sep=',', encoding='utf-8')
                    
            except AmbiguousTimeError:
                logger.warn('Error retrieving measurement data due to daylight savings timestamps for forecast: %s', forecast.key)


if __name__ == '__main__':
    main()