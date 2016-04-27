#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import os
import json
import numpy as np
import pandas as pd
import pvlib as pv

from configparser import ConfigParser


def read(latitude, longitude, altitude, timezone):
    systems = {}
    
    here = os.path.abspath(os.path.dirname(__file__))
    settings = os.path.join(os.path.dirname(here), 'conf', 'systems.cfg')
    config = ConfigParser()
    config.read(settings)
    
    loc = pv.location.Location(latitude, longitude, timezone, altitude)
    for section in config.sections():
        system = System(loc, section, config)
        systems[section] = system

    return systems


class System:
    def __init__(self, location, id, parameters):
        self.location = location
        self.id = id
        
        self.modules_param = {}
        for (key, value) in parameters.items(id):
            self.modules_param[key] = self._parse_parameter(value)
        
        self.system_param = self._load_parameters()
      
    
    def save_parameters(self):
        here = os.path.abspath(os.path.dirname(__file__))
        datadir = os.path.join(here, "data")
        paramfile = os.path.join(datadir, self.id.lower() + '.cfg')
        
        params_var = {}
        params_var['eta'] = self.system_param['eta']
        params_var['cov'] = self.system_param['cov']
        
        with open(paramfile, 'w') as paramjson:
            json.dump(params_var, paramjson)
    
    
    def _load_parameters(self):
        here = os.path.abspath(os.path.dirname(__file__))
        paramfile_default = os.path.join(os.path.dirname(here), 'conf', 'systems_param.cfg')
        config = ConfigParser()
        config.read(paramfile_default)
        
        params = {}
        for (key, value) in config.items('Default'):
            params[key] = self._parse_parameter(value)
        
        
        datadir = os.path.join(here, "data")
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
        