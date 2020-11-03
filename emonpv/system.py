# -*- coding: utf-8 -*-
"""
    emonpv.system
    ~~~~~~~~~~~~~
    
    
"""
import logging
logger = logging.getLogger(__name__)

import os
import pandas as pd
import datetime as dt

from th_e_core import Forecast, ConfigUnavailableException
from th_e_core.weather import Weather, TMYWeather, EPWWeather
from th_e_core.pvsystem import PVSystem
from th_e_core.system import System as SystemCore

from pvlib.location import Location
from configparser import ConfigParser
from emonpv.database import ModuleDatabase, InverterDatabase
from emonpv.model import Model


class System(SystemCore):

    def _activate(self, components, configs, **kwargs):
        super()._activate(components, configs, **kwargs)
        try:
            self.weather = Forecast.read(self, **kwargs)
            
        except ConfigUnavailableException:
            # Use weather instead of forecast, if forecast.cfg not present
            self.weather = Weather.read(self, **kwargs)
        
        if isinstance(self.weather, TMYWeather):
            self.location = Location.from_tmy(self.weather.meta)
        elif isinstance(self.weather, EPWWeather):
            self.location = Location.from_epw(self.weather.meta)
        else:
            self.location = self._location_read(configs, **kwargs)

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
        
        weather = self.weather.get(*args, **kwargs)
        
        result_columns = ['pv_power']
        results = pd.DataFrame(columns=result_columns, index=weather.index).fillna(0)
        results.index.name = 'Time'
        
        if len(self) > 0:
            logger.info("Starting simulation for system: %s", self.name)
            start = dt.datetime.now()
            
            for configs in self.values():
                if configs.type == 'pv':
                    model = Model.read(self, configs, **kwargs)
                    result = model.run(weather, **kwargs)
                    results['pv_power'] += result
                    
                    if self._database is not None:
                        self._database.persist(result, **kwargs)
            
            logger.info('Simulation complete')
            logger.debug('Simulation complete in %i seconds', (dt.datetime.now() - start).total_seconds())
        
        return pd.concat([results, weather], axis=1)


class Configurations(PVSystem):

    def _configure(self, configs, **kwargs):
        super()._configure(configs, **kwargs)
        
        self.module_parameters = self._configure_module(configs)
        self.inverter_parameters = self._configure_inverter(configs)

    def _configure_module(self, configs):
        module = {}
        
        if 'type' in configs['Module']:
            type = configs['Module']['type'] #@ReservedAssignment
            modules = ModuleDatabase(configs)
            module = modules.get(type)
        
        def module_update(items):
            for key, value in items:
                try:
                    module[key] = float(value)
                except ValueError:
                    module[key] = value
        
        if configs.has_section('Parameters'):
            module_update(configs.items('Parameters'))
        
        module_file = os.path.join(configs['General']['config_dir'], 
                                   configs['General']['id']+'.d', 'module.cfg')
        
        if os.path.exists(module_file):
            with open(module_file) as f:
                module_str = '[Module]\n' + f.read()
            
            module_configs = ConfigParser()
            module_configs.optionxform = str
            module_configs.read_string(module_str)
            module_update(module_configs.items('Module'))
        
        if 'pdc0' not in module:
            module['pdc0'] = module['I_mp_ref'] \
                           * module['V_mp_ref']
        
        return module

    def _configure_inverter(self, configs):
        inverter = {}
        
        if 'type' in configs['Inverter']:
            type = configs['Inverter']['type'] #@ReservedAssignment
            inverters = InverterDatabase(configs)
            # TODO: Test and verify inverter CEC parameters
            #inverter = inverters.get(type)
        
        def inverter_update(items):
            for key, value in items:
                try:
                    inverter[key] = float(value)
                except ValueError:
                    inverter[key] = value
        
        inverter_file = os.path.join(configs['General']['config_dir'], 
                                     configs['General']['id']+'.d', 'inverter.cfg')
        
        if os.path.exists(inverter_file):
            with open(inverter_file) as f:
                inverter_str = '[Inverter]\n' + f.read()
            
            inverter_configs = ConfigParser()
            inverter_configs.optionxform = str
            inverter_configs.read_string(inverter_str)
            inverter_update(inverter_configs.items('Inverter'))
        
        if 'pdc0' not in inverter and 'pdc0' in self.module_parameters and \
                configs.has_section('Inverter'):
            total = configs.getfloat('Inverter', 'strings') \
                  * configs.getfloat('Module', 'count')
            
            inverter['pdc0'] = self.module_parameters['pdc0']*total
        
        return inverter

