# -*- coding: utf-8 -*-
"""
    emonpv.system
    ~~~~~~~~~~~~~
    
    
"""
import logging
logger = logging.getLogger(__name__)

from th_e_core import System as S
from th_e_core import Model, Forecast, ConfigUnavailableException
from th_e_core.weather import Weather, TMYWeather, EPWWeather
from th_e_core.pvsystem import PVSystem

from pvlib.location import Location
from emonpv.database import ModuleDatabase #, InverterDatabase


class System(S):

    def _activate(self, components, **kwargs):
        super()._activate(components, **kwargs)
        try:
            self._weather = Weather.read(self, **kwargs)
            
            if isinstance(self._weather, TMYWeather):
                self._location = Location.from_tmy(self._weather.meta)
            elif isinstance(self._weather, EPWWeather):
                self._location = Location.from_epw(self._weather.meta)
            else:
                self._location = self._location_read(self._configs, **kwargs)
            
        except ConfigUnavailableException:
            self._location = self._location_read(self._configs, **kwargs)
            self._weather = Forecast.read(self, **kwargs)
        
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
        if isinstance(self._weather, Forecast):
            return self._weather
        
        raise AttributeError("System forecast not configured")

    @property
    def _component_types(self):
        return super()._component_types + ['modules']

    def _component(self, configs, type, **kwargs): #@ReservedAssignment
        if type in ['pv', 'modules']:
            return Modules(configs, self, **kwargs)
        
        return super()._component(configs, type, **kwargs)

    def run(self, *args, **kwargs):
        data = self._model.run(self._weather.get(*args, **kwargs), **kwargs)
        
        if self._database is not None:
            self._database.persist(data, **kwargs)
        
        return data


class Modules(PVSystem):

    def _init_parameters(self, configs, system, *args):
        if not configs.has_option('Modules', 'type'):
            return super()._init_parameters(configs, system, *args)
        
        modules = ModuleDatabase(system._configs)
        module = modules.get(configs.get('Modules', 'type'))
        
        inverter = {}
        if configs.has_section('Inverter') and 'pdc0' in module:
            total = configs.getfloat('Inverter', 'strings') \
                    *configs.getfloat('Modules', 'count') \
                    *configs.getfloat('General', 'count')
            
            inverter['pdc0'] = module['pdc0']*total
        
        return { 'module_parameters': module,
                 'inverter_parameters': inverter }

