#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""    
    Optimizes the prediction parameters of a photovoltaic energy systems, according to solar irradiance forecasts
    
"""
import logging
logger = logging.getLogger('pvprediction')

import os
import datetime

from configparser import ConfigParser

import numpy as np
import pandas as pd
import pvprediction as pv
from pvprediction.emoncms import Emoncms
from pvprediction.irradiation import Irradiation


def main(args=None):
    here = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    settingsfile = os.path.join(os.path.dirname(here), 'conf', 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    emoncms = Emoncms(settings.get("Emoncms","URL"), settings.get("Emoncms","APIkey"))
    
    systemlist = pv.systems.read(float(settings.get('Location','latitude')), 
                                 float(settings.get('Location','longitude')), 
                                 float(settings.get('Location','altitude')),
                                 str(settings.get('Location','timezone')))
    
    referencedir = os.path.join(os.path.dirname(here), 'ref')
    
    forecast = pv.irradiation.forecast(datetime.datetime.now(), 
                                       settings.get('Location','timezone'), 
                                       var=os.path.join(referencedir, settings.get("DWD","key")), 
                                       method='DWD_CSV')
    
    dwd_meas = pv.irradiation.reference(datetime.datetime.now(), 
                                        settings.get('Location','timezone'), 
                                        var=settings.get("DWD","id"), 
                                        method='DWD_PUB')
    
    reference = None
    measurements = pd.Series(np.nan, name='measurements')
    start = forecast.times[0]
    for i in range(-29, 1):
        time = start + pd.DateOffset(days=i)
        forecast = pv.irradiation.forecast(time, 
                                           settings.get('Location','timezone'), 
                                           var=os.path.join(referencedir, settings.get("DWD","key")), 
                                           method='DWD_CSV')
        
        logger.info('Starting optimized prediction for forecast: %s', forecast.id)
        for id, sys in systemlist.items():
            times = forecast.times - pd.DateOffset(days=1)
            if reference is None:
                reference = Irradiation(id + '_dwd', times, 
                                        dwd_meas.global_horizontal[times], dwd_meas.diffuse_horizontal[times], dwd_meas.temperature[times],
                                        method=dwd_meas.method)
            
            if measurements.empty or not measurements.index.equals(times):
                measurements, meas_detailed = emoncms.feed('device' + sys.id.lower() + '_out_power', times, settings.get('Location','timezone'))
                measurements.name = 'measurements'
            
            if not measurements.empty and measurements.index.equals(times):
                result = pv.predict.optimize(sys, reference, measurements, float(settings.get('Optimization','forgetting')))
                
                eta = pd.Series(np.nan, index=forecast.times, name='eta')
                for i in eta.index:
                    eta.ix[i] = result[i.tz_convert('UTC').hour]
                
                measurements, meas = emoncms.feed('device' + sys.id.lower() + '_out_power', forecast.times, settings.get('Location','timezone'))
                measurements.name = 'measurements'
                
                reference = Irradiation(id + '_dwd', forecast.times, 
                                        dwd_meas.global_horizontal[forecast.times], dwd_meas.diffuse_horizontal[forecast.times], dwd_meas.temperature[forecast.times],
                                        method=dwd_meas.method)
                
                est_eff = pv.predict.power_effective(sys, reference)
                est = est_eff*eta*sys.modules_param['n']
                est.name = 'estimation'
                
                datadir = os.path.join(os.path.dirname(here), 'data')
                filename = forecast.id + '_ref_' + id + '.csv';
                filepath = os.path.join(datadir, filename)
                
                error = pd.Series(measurements - est, name='innovation')
                sim = pd.concat([measurements, est, error], axis=1)
                sim.to_csv(filepath, sep=',', encoding='utf-8')
                
                
                
                est_eff = pv.predict.power_effective(sys, forecast)
                est = est_eff*eta*sys.modules_param['n']
                est.name = 'estimation'
                
                filename = forecast.id + '_opt_' + id + '.csv';
                filepath = os.path.join(datadir, filename)
                
                error = pd.Series(measurements - est, name='innovation')
                sim = pd.concat([measurements, est, error], axis=1)
                sim.to_csv(filepath, sep=',', encoding='utf-8')
                
                innovationfile = os.path.join(datadir, 'innovation.csv')
                if os.path.isfile(innovationfile):
                    innovation = pd.read_csv(innovationfile, index_col='hours', encoding='utf-8')
                else:
                    innovation = pd.DataFrame()
                error.name = forecast.id
                error.index = error.index.hour
                error.index.name = 'hours'
                innovation = pd.concat([innovation, error], axis=1)
                innovation.to_csv(innovationfile, sep=',', encoding='utf-8')
                
                efficiencyfile = os.path.join(datadir, 'efficiency.csv')
                if os.path.isfile(efficiencyfile):
                    efficiency = pd.read_csv(efficiencyfile, index_col='hours', encoding='utf-8')
                else:
                    efficiency = pd.DataFrame()
                eta.name = forecast.id
                eta.index = eta.index.hour
                eta.index.name = 'hours'
                efficiency = pd.concat([efficiency, eta], axis=1)
                efficiency.to_csv(efficiencyfile, sep=',', encoding='utf-8')


if __name__ == '__main__':
    main()