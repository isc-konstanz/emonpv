# -*- coding: utf-8 -*-
"""
    pvforecast.system
    ~~~~~
    
    This module provides functions to read the defined :class:`pvforecast.System` list 
    from either a server or a configuration file. SystemList contain information about location, 
    orientation and datasheet parameters of a specific photovoltaic installation.
    
"""
import logging
logger = logging.getLogger('pvforecast.systems')

import os
import pandas as pd

from configparser import ConfigParser
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from .model import ModelChain


class SystemList(list):

    def __init__(self, configs, database, **kwargs):
        super(SystemList, self).__init__(**kwargs)
        
        self.database = database
        self.read_config(configs)


    def forecast(self, weather, date):
        for system in self:
            forecast = system.forecast(weather.forecast(system, date))
            
            self.database.post(system, forecast)


    def read_config(self, configs):
        from pvlib.pvsystem import retrieve_sam
        
        datadir = configs.get('General', 'datadir')
        systemsfile = os.path.join(configs.get('General', 'configdir'), 'systems.cfg')
        systems = ConfigParser()
        systems.read(systemsfile)
        
        modules = retrieve_sam(path=os.path.join(datadir, 'modules', 'cec_sandia.csv'))
        inverters = retrieve_sam(path=os.path.join(datadir, 'inverters', 'cec.csv'))
        
        for name in systems:
            if name != 'DEFAULT':
                config = {}
                module = None
                inverter = None
                
                for key in systems.options(name):
                    value = systems.get(name, key)
                    
                    if key == 'module_name' and value != '':
                        module = modules[value]
                    elif key == 'inverter_name' and value != '':
                        inverter = inverters[value]
                    else:
                        config[key] = systems.get(name, key)
                
                system_name = None
                if name[-1].isdigit():
                    system_name = name[:name.rfind('_')]
                else:
                    system_name = name
                
                for s in self:
                    if system_name == s.name:
                        system = s
                        break
                else:
                    system = System(system_name, config)
                    
                    self.append(system)
                
                system.append(name, config, module, inverter)


class System(list):

    def __init__(self, name, system, **kwargs):
        super(System, self).__init__(**kwargs)
        
        self.name = name
        self.apikey = None
        
        latitude = float(system['latitude'])
        longitude = float(system['longitude'])
        altitude = float(system['altitude'])
        
        self.location_key = str(latitude) + '_' + str(longitude)
        self.location = Location(latitude, longitude, altitude=altitude, 
                                 tz=system['timezone'], 
                                 name=name)


    def append(self, name, config, module, inverter):
        
        if inverter is None:
            inverter = {}
#             if 'pdc0' not in module:
#                 module['pdc0'] = 1
        
        super(System, self).append(PVSystem(surface_tilt = float(config['tilt']), 
                                            surface_azimuth = float(config['azimuth']), 
                                            albedo = float(config['albedo']), 
                                            modules_per_string = int(config['modules']), 
                                            strings_per_inverter = int(config['strings']), 
                                            module_parameters = module, inverter_parameters = inverter, 
                                            name = name))


    def forecast(self, weather):
        forecast = pd.DataFrame()
        
        for system in self:
            model = ModelChain(system, self.location)
            model.run_model(weather.index, weather=weather);
            
            result = model.ac
            result.name = system.name.lower()
            forecast = pd.concat([forecast, result.where(result > 1e-6, other=0)], axis=1)
        
        if len(forecast.columns) > 1:
            forecast[self.name] = forecast.sum(axis=1)
        
        return forecast

