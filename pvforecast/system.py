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
import json
import pandas as pd
import pvlib as pv

from configparser import ConfigParser
from .database import ModuleDatabase
from .model import ModelChain


class SystemList(list):

    def __init__(self, configs, database, **kwargs):
        super(SystemList, self).__init__(**kwargs)
        
        self.database = database
        self.__init_config(configs)


    def __init_config(self, configs):
        self.modules = ModuleDatabase(configs)
        
        datadir = configs.get('General', 'datadir')
        
        with open(os.path.join(configs.get('General', 'configdir'), 'systems.json')) as systemsfile:
            systems = json.load(systemsfile)
#         if 'emoncms' in self.database:
#             systems = self.database['emoncms'].connection._request_json('solar/config.json?')
#             with open(os.path.join(configs.get('General', 'configdir'), 'systems.json'), 'w') as systemsfile:
#                 json.dump(systems, systemsfile, indent=4)
            for config in systems:
                system = System(config['name'], config, datadir)
                
                for group in config['modules']:
                    module = self.modules.get(group['module'])
                    inverter = None
                    
                    system.append(group['name'], group, module, inverter)
                
                self.append(system)
#         else:
#             self.__read_ini(configs)


    def __read_ini(self, configs):
        from pvlib.pvsystem import retrieve_sam
        
        datadir = configs.get('General', 'datadir')
        
        systemsfile = os.path.join(configs.get('General', 'configdir'), 'systems.cfg')
        systems = ConfigParser()
        systems.read(systemsfile)
        
        inverters = retrieve_sam(path=os.path.join(datadir, 'inverters', 'cec_sam.csv'))
        
        for name in systems:
            if name != 'DEFAULT':
                config = {}
                module = None
                inverter = None
                
                for key in systems.options(name):
                    value = systems.get(name, key)
                    
                    if key == 'module' and value != '':
                        module = self.modules.get(value)
                    elif key == 'inverter' and value != '':
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
                    system = System(name, config, datadir)
                    
                    self.append(system)
                
                system.append(name, config, module, inverter)


    def forecast(self, weather, time, model=None, state=None, interval=60):
        time = pd.to_datetime(time, utc=True)
        locations = {}
        for system in self:
            loc = system.grid_location(weather)
            if not loc in locations:
                locations[loc] = []
            
            locations[loc].append(system)
            
        # TODO: Implement multi threading
        for systems in locations.values():
            for system in systems:
                if model is None or state is None:
                    forecast = system.forecast(weather.forecast(system, time))
                else:
                    forecast = system.forecast_NN(weather.forecast(system, time), model, state)
                self.database.persist(system, forecast, date=time)
        
        
        if model is not None and state is not None:
            # select only those inputs that have measurements available
            dX = {k: [[v[m][j] for j in range(len(v[m])) if j+(interval/60) < (len(v)-m)*(interval/60)] for m in range(len(v))] for k, v in state.items()}

            # add the new measurements
            for k, v in dX.items():
                for j in range(len(v)):
                    for h in range(len(v[j])):
                        if v[j][h][1] == -1:
                            v[j][h][1] = -2-h # TODO: set the correct new measurements
            
            # format training input and train model
            num_sys = len(dX.keys())
            import numpy as np
            dX = np.stack(dX.values(), axis=1).reshape(-1)[:-num_sys]
            if len(dX) > 0:
                X, y = map(list, zip(*[(d[0][0], d[0][1]) for d in dX]))
                X = np.array(X)
                X = X.reshape(X.shape[0]*X.shape[1], X.shape[2], X.shape[3])
                y = np.array(y)
                if len(X) > num_sys:
                    model.train_model(X, y)
                    model.save_model('model_' + str(time.year) + '_' + str(time.month) + '_' + str(time.day) + '_' + str(time.hour))


class System(list):

    def __init__(self, name, config, datadir, **kwargs):
        super(System, self).__init__(**kwargs)
        
        self.name = name
        self.apikey = config['apikey'] if 'apikey' in config else None
        
        latitude = float(config['latitude'])
        longitude = float(config['longitude'])
        altitude = float(config['altitude'])
        timezone = config['timezone'] if 'timezone' in config else 'UTC'
        
        self.location_grid = False
        self.location_key = '{0:.5f}'.format(latitude) + '_' + '{0:.5f}'.format(longitude)
        self.location = Location(latitude, longitude, altitude=altitude, 
                                 tz=timezone, 
                                 name=self.name)
        
        self.location_dir = os.path.join(datadir, 'systems', self.location_key)
        if not os.path.exists(self.location_dir):
            os.makedirs(self.location_dir)
        
        self._load_location()


    def append(self, name, config, module, inverter):
        if inverter is None:
            inverter = {}
        
        super(System, self).append(pv.pvsystem.PVSystem(surface_tilt = float(config['tilt']), 
                                                        surface_azimuth = float(config['azimuth']), 
                                                        albedo = float(config['albedo']), 
                                                        modules_per_string = int(config['modules_per_string']), 
                                                        strings_per_inverter = int(config['strings_per_inverter']), 
                                                        module_parameters = module, 
                                                        inverter_parameters = inverter, 
                                                        name = name))


    def forecast(self, weather):
        forecast = pd.DataFrame()
        
        for system in self:
            model = ModelChain(system, self.location)
            model.run_model(weather.index, weather=weather);
            
            result = model.ac
            result.name = system.name.lower()
            forecast = pd.concat([forecast, result.where(result > 1e-6, other=0)], axis=1)
        
        if len(forecast.columns) == 1:
            forecast.columns = [self.name]
        
        elif len(forecast.columns) > 1:
            columns = [self.name] + list(forecast.columns)
            forecast[self.name] = forecast.sum(axis=1)
            forecast = forecast.reindex_axis(columns, axis=1)
        
        return forecast
        
    
    def forecast_NN(self, weather, model, state):
        forecast = pd.DataFrame()
        sliding_window = 236
        for system in self:
            input, idx = model.create_input(weather, system, self.location)
            inputs, result = model.predict(input)
            result = result.set_index(idx)[0]
            result.name = system.name.lower()
            forecast = pd.concat([forecast, result.where(result > 1e-6, other=0)], axis=1)
            
            # save prediction inputs for later training
            if system.name in state:
                state[system.name].append(inputs)
                while len(state[system.name]) > sliding_window:
                    state[system.name].pop(0)
            else:
                state[system.name] = [inputs]
        
        if len(forecast.columns) == 1:
            forecast.columns = [self.name]
        
        elif len(forecast.columns) > 1:
            columns = [self.name] + list(forecast.columns)
            forecast[self.name] = forecast.sum(axis=1)
            forecast = forecast.reindex(columns, axis=1)
        
        return forecast


    def grid_location(self, weather):
        if not self.location_grid:
            meta = weather.server.get_meta(self.location)
            
            self.location = self._write_location({
                    'latitude': float(meta['latitude']),
                    'longitude': float(meta['longitude']),
                    'altitude': float(meta['height']),
                })
        
        return self.location


    def _load_location(self):
        file = os.path.join(self.location_dir, 'location.json')
        if not os.path.exists(file):
            return
        
        with open(file, encoding='utf-8') as f:
            self.location = self._parse_location(json.load(f))
            self.location_grid = True


    def _write_location(self, location):
        file = os.path.join(self.location_dir, 'location.json')
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(location, f)
            
            return self._parse_location(location)


    def _parse_location(self, location):
        return Location(location['latitude'], location['longitude'], altitude=location['altitude'], 
                        tz=self.location.tz, 
                        name=self.name)


class Location(pv.location.Location):

    def __attrs(self):
        return (self.latitude, self.longitude, self.altitude)

    def __eq__(self, other):
        return isinstance(other, Location) and self.__attrs() == other.__attrs()

    def __hash__(self):
        return hash(self.__attrs())

