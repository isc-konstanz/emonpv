#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""    
    Optimises the prediction parameters of a photovoltaic energy systems, according to solar irradiance forecasts
    
"""
import logging
logger = logging.getLogger('pvprediction')

import os
import pandas as pd
import pvprediction as pv
from pvprediction import tools
from pvprediction import Emoncms

from configparser import ConfigParser


def main(args=None):
    here = os.path.abspath(os.path.dirname(__file__))
    args = tools.get_parser().parse_args()
    
    forecastfile = args.forecastfile
    if (args.forecastdir != None):
        forecastdir = args.forecastdir
    else:
        forecastdir = os.path.join(os.path.dirname(os.path.dirname(here)), 'forecast')
    
    settingsfile = os.path.join(os.path.dirname(here), 'conf', 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    
    emoncms = Emoncms(settings.get("Emoncms","URL"), settings.get("Emoncms","APIkey"))
    
    systemlist = pv.systems.read(float(settings.get('Location','latitude')), 
                                 float(settings.get('Location','longitude')), 
                                 float(settings.get('Location','altitude')),
                                 str(settings.get('Location','timezone')))
    
    
    irradiation = pv.irradiation.read(settings.get('DWD','id'), settings.get('Location','timezone'), method='DWD')
    
    start = irradiation.times[0]
    for i in range(0, 31):
        if i > 0:
            time = start + pd.DateOffset(days=i)
            forecastfile = pv.irradiation.get_filename(time, settings.get("DWD","key"))
            forecast = pv.irradiation.read(os.path.join(forecastdir, forecastfile), settings.get('Location','timezone'))
        
        logger.info('Starting optimized prediction for forecast: %s', forecast.id)
        for id, sys in systemlist.items():
            times = forecast.times - pd.DateOffset(days=1)
            ref, meas = emoncms.feed(sys.id, times, settings.get('Location','timezone'))
            
            if not ref.empty and ref.index.equals(times):
                pv.predict.optimize(sys, forecast, ref, float(settings.get('Optimization','forgetting')))
            
            if (args.simulationdir != None):
                simulationdir = args.simulationdir
                
                ref, meas = emoncms.feed(sys.id, forecast.times, settings.get('Location','timezone'))
                ref.name = 'reference'
                
                est = pv.predict.power_system(sys, forecast)
                est.name = 'estimation'
                
                error = pd.Series(ref - est, name='innovation')
                sim = pd.concat([ref, est, error], axis=1)
                
                simulationname = forecast.id + '_opt_' + id + '.csv';
                simulationfile = os.path.join(simulationdir, simulationname)
                
                sim.to_csv(simulationfile, sep=',', encoding='utf-8')
                
                
                innovationfile = os.path.join(simulationdir, 'Innovation_opt.csv')
                if os.path.isfile(innovationfile):
                    opt = pd.read_csv(innovationfile, index_col='hours', encoding='utf-8')
                else:
                    opt = pd.DataFrame()
                error.name = forecast.id
                error.index = error.index.hour
                error.index.name = 'hours'
                opt = pd.concat([opt, error], axis=1)
                opt.to_csv(innovationfile, sep=',', encoding='utf-8')


if __name__ == '__main__':
    main()