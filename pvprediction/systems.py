#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import os
import math
import numpy as np
import pandas as pd
import pvlib as pv

import datetime

from configparser import ConfigParser
import json


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
        
        self.system_param = self._load_parameters(id)
            
    
    def irradiation(self, forecast):
        """ 
            Calculates the global irradiation on a tilted surface, consisting out of the sum of
            direct, diffuse and reflected irradiance components.
            
            :param forecast: The solar irradiation forecast on a horizontal surface.
            
        """
        pressure = pv.atmosphere.alt2pres(self.location.altitude)
        
        # Get the solar angles, determining the suns irradiation on a surface by an implementation of the NREL SPA algorithm
        angles = self._mean_solarangles(forecast.index, pressure)
        
        # Prevent sign errors and determine global and direct normal irradiance as defined by Quaschning
        forecast = np.absolute(forecast)
        forecast['normal'] = forecast['direct']*(1/np.sin(np.deg2rad(angles['elevation']))).fillna(0)
        forecast['global'] = forecast['direct'] + forecast['diffuse']
        
        direct = forecast['normal']*(np.cos(np.deg2rad(angles['incidence']))).fillna(0)
        
        
        # Determine extraterrestrial radiation and airmass
        extra = pv.irradiance.extraradiation(forecast.index)
        airmass_rel = pv.atmosphere.relativeairmass(angles['apparent_zenith'])
        airmass = pv.atmosphere.absoluteairmass(airmass_rel, pressure)
        
        diffuse = pv.irradiance.perez(surface_tilt=self.modules_param['tilt'], surface_azimuth=self.modules_param['azimuth'], 
                                      solar_zenith=angles['apparent_zenith'], solar_azimuth=angles['azimuth'], 
                                      dhi=forecast['diffuse'], dni=forecast['normal'], dni_extra=extra, 
                                      airmass=airmass)
        
        reflected = pv.irradiance.grounddiffuse(surface_tilt=self.modules_param['tilt'], 
                                                ghi=forecast['global'], 
                                                albedo=self.modules_param['albedo'])
        
        # Calculate the total irradiation, using the perez model
#         irradation = pv.irradiance.total_irrad(surface_tilt=self.modules_param['tilt'], surface_azimuth=self.modules_param['azimuth'], 
#                                                solar_zenith=angles['apparent_zenith'], solar_azimuth=angles['azimuth'], 
#                                                dni=forecast['normal'], ghi=forecast['global'], dhi=forecast['diffuse'], 
#                                                dni_extra=extra, airmass=airmass, 
#                                                surface_type=self.modules_param['albedo'], 
#                                                model='perez')
        
        
        # Calculate total irradiation and replace values smaller than specific threshold
        # Check if still necessary, for better forecasts
        total = direct + diffuse.fillna(0) + reflected
        total.loc[total < 0.01] = 0
        
        return pd.Series(total.fillna(0), index=forecast.index, name='irradiation')
    
    
    def _mean_solarangles(self, range, pressure):
        pd.options.mode.chained_assignment = None  # default='warn'
        
        start = range[0] + pd.DateOffset(minutes=-30)
        end = range[-1] + pd.DateOffset(minutes=30)
        timestamps = pd.date_range(start, end, freq='min')
        solarposition = pv.solarposition.get_solarposition(timestamps, self.location, pressure=pressure)
        solarposition['incidence'] = pv.irradiance.aoi(self.modules_param['tilt'], self.modules_param['azimuth'], 
                                                        solarposition['zenith'], solarposition['azimuth'])
        
        # Average +/- 30min, to get hourly reference values
        avg = pd.DataFrame(np.nan, index=range, columns=solarposition.columns)
        for time in avg.index:
            start = time + pd.DateOffset(minutes=-30)
            end = time + pd.DateOffset(minutes=30)
            data = solarposition.ix[start:end]
            
            # Discard elevation and incidence values lower than 0, to avoid ignoring the sunrise on the surface
            data.loc[data['apparent_elevation'] < 0, 'apparent_elevation'] = np.nan
            data.loc[data['elevation'] < 0, 'elevation'] = np.nan
            data.loc[data['incidence'] > 90, 'incidence'] = np.nan
            
            avg.ix[time] = data.mean()
    
        return avg
    
    
    def _load_parameters(self, id):
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
        
        paramfile = os.path.join(datadir, id.lower() + '.cfg')
        if (os.path.isfile(paramfile)):
            paramjson = open(paramfile)
            params_var = json.load(paramjson)
            params.update(params_var)
        else:
            params_var = {}
            params_var['eta'] = params['eta']
            params.update(params_var)
            
            with open(paramfile, 'w') as paramjson:
                json.dump(params_var, paramjson)
            
        return params
    
    
    def _parse_parameter(self, parameter):
        try:
            return int(parameter)
        except ValueError:
            return float(parameter)
        