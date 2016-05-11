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


def read(configdir, latitude, longitude, altitude, timezone):
    systems = {}
    
    configfile = os.path.join(configdir, 'systems.cfg')
    config = ConfigParser()
    config.read(configfile)
    
    loc = pv.location.Location(latitude, longitude, tz=timezone, altitude=altitude)
    for section in config.sections():
        logger.debug('System "%s" found', section)
        
        system = System(configdir, section, config, loc)
        systems[section] = system

    return systems


class System:
    def __init__(self, configdir, sysid, parameters, location):
        self.id = sysid
        self.location = location
        
        self.modules_param = {}
        for (key, value) in parameters.items(sysid):
            self.modules_param[key] = self._parse_parameter(value)
        
        self.system_param = self._load_parameters(configdir)
      
    
    def save_parameters(self):
        here = os.path.abspath(os.path.dirname(__file__))
        datadir = os.path.join(here, "data")
        paramfile = os.path.join(datadir, self.id.lower() + '.cfg')
        
        params_var = {}
        params_var['eta'] = self.system_param['eta']
        params_var['cov'] = self.system_param['cov']
        
        with open(paramfile, 'w') as paramjson:
            json.dump(params_var, paramjson)
    
    
    def _load_parameters(self, configdir):
        here = os.path.abspath(os.path.dirname(__file__))
        datadir = os.path.join(here, "data")
        
        defaultfile = os.path.join(configdir, 'system_default.cfg')
        config = ConfigParser()
        config.read(defaultfile)
        
        params = {}
        for (key, value) in config.items('Default'):
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
        