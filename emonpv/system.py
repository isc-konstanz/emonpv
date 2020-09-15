# -*- coding: utf-8 -*-
"""
    emonpv.system
    ~~~~~~~~~~~~~
    
    
"""
import logging
logger = logging.getLogger(__name__)

import os

from th_e_core import System as SystemCore
from th_e_core import Model, Forecast
from th_e_core.weather import Weather, TMYWeather, EPWWeather
from th_e_core.pvsystem import PVSystem

from pvlib.location import Location
from configparser import ConfigParser
from emonpv.database import ModuleDatabase #, InverterDatabase


class System(SystemCore):

    def _activate(self, components, *args, **kwargs):
        super()._activate(components, *args, **kwargs)
        
        self.weather = Weather.read(self, **kwargs)
        if isinstance(self.weather, TMYWeather):
            self.location = Location.from_tmy(self.weather.meta)
        elif isinstance(self.weather, EPWWeather):
            self.location = Location.from_epw(self.weather.meta)
        
        self._model = Model.read(self, **kwargs)

    def _location_read(self, configs, **kwargs):
        return Location(configs.getfloat('Location', 'latitude'), 
                        configs.getfloat('Location', 'longitude'), 
                        tz=configs.get('Location', 'timezone', fallback='UTC'), 
                        altitude=configs.getfloat('Location', 'altitude', fallback=0), 
                        name=self.name, 
                        **kwargs)

    @property
    def _forecast(self):
        if isinstance(self.weather, Forecast):
            return self.weather
        
        raise AttributeError("System forecast not configured")

    @property
    def _component_types(self):
        return super()._component_types + ['modules', 'configs']

    def _component(self, configs, type, **kwargs): #@ReservedAssignment
        if type in ['pv', 'modules', 'configs']:
            return Configurations(configs, self, **kwargs)
        
        return super()._component(configs, type, **kwargs)

    def run(self, *args, **kwargs):
        data = self._model.run(self.weather.get(*args, **kwargs), **kwargs)
        
        if self._database is not None:
            self._database.persist(data, **kwargs)
        
        return data


class Configurations(PVSystem):

    def _configure(self, configs, **_):
        with open(os.path.join(configs['General']['config_dir'], configs['General']['id']+'.d', 'module.cfg')) as f:
            module_file = '[Module]\n' + f.read()
        
        module_configs = ConfigParser()
        module_configs.optionxform = str
        module_configs.read_string(module_file)
        
        self.module_parameters = {}
        for key, value in module_configs.items('Module'):
            try:
                self.module_parameters[key] = float(value)
                
            except ValueError:
                self.module_parameters[key] = value
        
        self.inverter_parameters = {}
        if configs.has_section('Inverter') and 'pdc0' in self.module_parameters:
            total = configs.getfloat('Inverter', 'strings') \
                  * configs.getfloat('Module', 'count')
            
            self.inverter_parameters['pdc0'] = float(self.module_parameters['pdc0'])*total

