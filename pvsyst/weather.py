# -*- coding: utf-8 -*-
"""
    pvsyst.weather
    ~~~~~
    
    This module provides functions to open :class:`pvsyst.Weather` objects, 
    used as reference to calculate a photovoltaic installations' generated power.
    The provided environmental data contains temperatures and horizontal 
    solar irradiation, which can be used, to calculate the effective irradiance 
    on defined, tilted photovoltaic systems.
    
"""
import logging
logger = logging.getLogger(__name__)

import os
import pytz as tz
import datetime as dt

from configparser import ConfigParser
from abc import ABC, abstractmethod
from core import Database
from pvlib.iotools import read_tmy2, read_tmy3


class Weather(ABC):

    def __init__(self, context, configs, **kwargs):
        from core import System
        if not isinstance(context, System):
            raise TypeError('Invalid weather type: {}'.format(type(context)))
        if not isinstance(configs, ConfigParser):
            raise ValueError('Invalid weather configuration type: {}'.format(type(configs)))
        
        self._context = context
        self._configs = configs
        self._configure(configs, **kwargs)
        self._open(context, **kwargs)

    def __repr__(self):
        configs = '[Weather]'
        for section in self._configs.sections():
            configs += '\n    [{}]'.format(section) + '\n'
            for (k, v) in self._configs.items(section):
                configs += '        {} = {}'.format(k, v) + '\n'
        
        return configs

    @staticmethod
    def open(system, **kwargs):
        from core import System
        if not isinstance(system, System):
            raise TypeError('Invalid weather system type: {}'.format(type(system)))
        
        config_dir = system._configs.get('General', 'config_dir')
        if not os.path.isdir(config_dir):
            raise ValueError('Invalid configuration directory: {}'.format(config_dir))
        
        config_file = os.path.join(config_dir, 'weather.cfg')
        if not os.path.isfile(config_file):
            raise ValueError('Unable to open model configurations: {}'.format(config_file))
        
        configs = ConfigParser()
        configs.read(config_file)
        
        if 'General' not in configs.sections():
            raise ValueError('Incomplete weather configuration. Unable to find general section')
        
        configs.set('General', 'root_dir', system._configs.get('General', 'root_dir'))
        configs.set('General', 'lib_dir', system._configs.get('General', 'lib_dir'))
        configs.set('General', 'data_dir', system._configs.get('General', 'data_dir'))
        configs.set('General', 'config_dir', config_dir)
        configs.set('General', 'config_file', config_file)
        
        if 'type' not in configs['General']:
            raise ValueError('Incomplete weather configuration. Unable to find weather type')
        
        model = configs.get('General', 'type').lower()
        if model == 'historic':
            return HistoricWeather(system, configs, **kwargs)
        
        elif model == 'tmy':
            return TMYWeather(system, configs, **kwargs)
        
        else:
            raise ValueError('Invalid weather type: {}'.format(model))

    def _open(self, system, **kwargs):
        pass

    def _configure(self, configs, **kwargs): #@UnusedVariable
        if logger.isEnabledFor(logging.DEBUG):
            print(self)

    @abstractmethod
    def get(self, **kwargs):
        pass


class HistoricWeather(Weather):

    def _configure(self, configs, **kwargs):
        super()._configure(configs, **kwargs)
        
        self._database = Database.open(configs, **kwargs)

    def get(self, start=None, stop=None, format='%d.%m.%Y', **kwargs): #@ReservedAssignment
        if start is None:
            start = tz.utc.localize(dt.datetime.utcnow())
            start.replace(year=start.year-1, month=1, day=1, hour=0, minute=0, second=0)
        elif isinstance(start, str):
            start = tz.utc.localize(dt.datetime.strptime(start, format))
        
        if stop is None:
            stop = start + dt.timedelta(days=364)
        elif isinstance(stop, str):
            stop = tz.utc.localize(dt.datetime.strptime(stop, format))
        
        return self._database.get(start=start, 
                                  stop=stop, 
                                  **kwargs)

class TMYWeather(Weather):

    def _configure(self, configs, **_):
        self.version = int(configs.get('General', 'version', fallback='3'))
        
        if 'file' in configs['TMY'] and not os.path.isabs(configs['TMY']['file']):
            configs['TMY']['file'] = os.path.join(configs['General']['data_dir'], 
                                                  configs['TMY']['file'])
        
        self.file = configs.get('TMY', 'file', fallback=None)
        self.year = configs.get('TMY', 'year', fallback=None)

    def _open(self, system, **kwargs): #@UnusedVariable
        if self.version == 3:
            self.data, self.meta = read_tmy3(filename=self.file, coerce_year=self.year)
            
        elif self.version == 2:
            self.data, self.meta = read_tmy2(self.file)
        else:
            raise ValueError('Invalid TMY version: {}'.format(self.version))

    def get(self, **_):
        # TODO: implement optional slicing
        return self.data

