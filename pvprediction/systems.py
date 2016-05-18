#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import logging
logger = logging.getLogger('pvprediction.systems')

import os
import json
import pvlib as pv

from configparser import ConfigParser


def read(configdir):
    systems = {}
    
    settingsfile = os.path.join(configdir, 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    configfile = os.path.join(configdir, 'systems.cfg')
    config = ConfigParser()
    config.read(configfile)
    
    loc = pv.location.Location(float(settings.get('Location','latitude')), 
                               float(settings.get('Location','longitude')), 
                               altitude=float(settings.get('Location','altitude')),
                               tz=str(settings.get('Location','timezone')))
    
    defaultfile = os.path.join(configdir, 'system_default.cfg')
    defaults = ConfigParser()
    defaults.read(defaultfile)
    
    for section in config.sections():
        logger.debug('System "%s" found', section)
        
        system = System(str(settings.get('General','datadir')), defaults.items('Default'), 
                        section, config, loc)
        
        systems[section] = system

    return systems


class System:
    def __init__(self, datadir, defaults, sysid, parameters, location):
        self.datadir = datadir
        
        self.id = sysid
        self.location = location
        
        self.modules_param = {}
        for (key, value) in parameters.items(sysid):
            self.modules_param[key] = self._parse_parameter(value)
        
        self.system_param = self._load_parameters(datadir, defaults)
      
    
    def save_parameters(self):
        here = os.path.abspath(os.path.dirname(__file__))
        datadir = os.path.join(here, "data")
        paramfile = os.path.join(datadir, self.id.lower() + '.cfg')
        
        params_var = {}
        params_var['eta'] = self.system_param['eta']
        params_var['cov'] = self.system_param['cov']
        
        with open(paramfile, 'w') as paramjson:
            json.dump(params_var, paramjson)
    
    
    def _load_parameters(self, datadir, default):
        params = {}
        for (key, value) in default:
            params[key] = self._parse_parameter(value)
        
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        
        paramfile = os.path.join(datadir, self.id.lower() + '.cfg')
        if (os.path.isfile(paramfile)):
            paramjson = open(paramfile)
            params_var = json.load(paramjson)
            params.update(params_var)
        else:
            params_var = {}
            params_var['eta'] = [params['eta']]*24
            params_var['cov'] = [params['sigma']**2]*24
            params.update(params_var)
            
            with open(paramfile, 'w') as paramjson:
                json.dump(params_var, paramjson)
            
        return params
    
    
    def _parse_parameter(self, parameter):
        try:
            return int(parameter)
        except ValueError:
            return float(parameter)
        