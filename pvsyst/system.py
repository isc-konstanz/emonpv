# -*- coding: utf-8 -*-
"""
    pvsyst.system
    ~~~~~
    
    This module provides functions to open the defined :class:`pvsyst.System` list 
    from either a server or a configuration file. Systems contain information about location, 
    orientation and datasheet parameters of a specific photovoltaic installation.
    
"""
import logging
logger = logging.getLogger('pvsyst.systems')

import pvlib as pv
import core

from pvsyst.weather import Weather, TMYWeather
from pvsyst.database import ModuleDatabase


class System(core.System):

    def _configure(self, configs, **kwargs):
        super()._configure(configs, **kwargs)
        
        self.weather = Weather.open(self, **kwargs)
        if isinstance(self.weather, TMYWeather):
            self.location = pv.location.Location.from_tmy(self.weather.meta)
        else:
            self.location = pv.location.Location(float(configs['Location']['latitude']), 
                                                 float(configs['Location']['longitude']), 
                                                 altitude=float(configs['Location']['altitude']), 
                                                 tz=configs['Location']['timezone'] or 'UTC', 
                                                 name=self.name, 
                                                 **kwargs)

    def _init_component(self, configs, **kwargs):
        return Modules(self, configs, **kwargs)

    @property
    def _component_types(self):
        return ['pv', 'modules']


class Modules(core.Component, pv.pvsystem.PVSystem):

    def __init__(self, system, configs, **kwargs):
        super().__init__(system, configs, 
                         name = configs['General']['id'], 
                         albedo = float(configs['General']['albedo']), 
                         surface_tilt = float(configs['Geometry']['tilt']), 
                         surface_azimuth = float(configs['Geometry']['azimuth']), 
                         modules_per_string = int(configs['Modules']['count']), 
                         strings_per_inverter = int(configs['Inverter']['strings']), 
                         **self._init_parameters(system, configs), 
                         **kwargs)

    def _init_parameters(self, system, configs):
        modules = ModuleDatabase(system._configs)
        module = modules.get(configs['Modules']['type'])
        
        total = configs.getfloat('Modules', 'count')*configs.getfloat('Inverter', 'strings')
        inverter = { 'pdc0': module['pdc0']*total }
        
        return { 'module_parameters': module,
                 'inverter_parameters': inverter }

    @property
    def type(self):
        return 'pv'

