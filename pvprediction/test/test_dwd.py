#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""    
    Optimises the prediction parameters of a photovoltaic energy systems, according to solar irradiance forecasts
    
"""
import logging
logger = logging.getLogger('pvprediction')

import os
import pvprediction as pv

from configparser import ConfigParser


def main(args=None):
    here = os.path.abspath(os.path.dirname(__file__))
    
    settingsfile = os.path.join(os.path.dirname(os.path.dirname(here)), 'conf', 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    irradiation = pv.irradiation.read(settings.get('DWD','id'), settings.get('Location','timezone'), method='DWD')
    
    simulationfile = os.path.join(os.path.dirname(os.path.dirname(here)), 'data', 'settings.cfg')
    irradiation.to_csv(simulationfile, sep=',', encoding='utf-8')


if __name__ == '__main__':
    main()