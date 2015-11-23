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

from datetime import timedelta

from configparser import ConfigParser
import json


def read(latitude, longitude, timezone):
    systems = {}
    
    here = os.path.abspath(os.path.dirname(__file__))
    settings = os.path.join(os.path.dirname(here), 'conf', 'systems.cfg')
    config = ConfigParser()
    config.read(settings)
    
    loc = pv.location.Location(latitude, longitude, timezone)
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
            
    
    def tilted_irradiance(self, forecast):
        """ 
            Calculates the global irradiance on a tilted surface, consisting out of the sum of
            direct, diffuse and reflected irradiance components.
        
            :param forecast: The solar irradiance forecast on a horizontal surface.
            
        """
        angles = self.solarangles(forecast.index)
        
        direct = np.abs(forecast['direct']*np.cos(np.deg2rad(angles['incidence']))/np.sin(np.deg2rad(angles['elevation'])))
        
        
        beam = np.abs(forecast['direct']/np.sin(np.deg2rad(angles['elevation'])))
        extra = pv.irradiance.extraradiation(forecast.index, self.system_param['solar_const'])
        airmass = pv.atmosphere.relativeairmass(angles['zenith'])
        diffuse = np.abs(pv.irradiance.perez(self.modules_param['tilt'], self.modules_param['orientation'], 
                                      forecast['diffuse'], beam, extra,
                                      angles['zenith'], angles['azimuth'], airmass))
        
        
        reflected = (forecast['direct'] + forecast['diffuse'])*self.system_param['albedo']*(1 - np.cos(self.modules_param['tilt']))/2
        
        
        # Replace values smaller than specific threshold
        # Check if still necessary, for better forecasts
        direct.loc[direct < 0.9] = 0
        diffuse.loc[direct < 0.9] = 0
        reflected.loc[direct < 0.9] = 0
        
        irradiance = pd.concat([direct, diffuse, reflected], axis=1, keys=['direct','diffuse','reflected']).fillna(0)
        
        irradiance['global'] = irradiance.sum(axis=1)
        return irradiance
        
    
    def solarangles(self, time):
        """ 
            Calculates the solar angles of a fixed tilted surface.
        
            :param time: The specific times, the angles should be calculated for.
            
        """
        angles = pd.DataFrame(data=np.nan, index=time, columns=['incidence', 'elevation', 'zenith', 'azimuth'])
        for t, row in angles.iterrows():
            day_of_year = t.timetuple().tm_yday
        
            # Calculate the equation of time in minutes, representing the difference between 
            # the fixed mean and the changing apparent solar times.
            b = math.radians((day_of_year - 1)*(360./365))
            time_equation = (180*4/math.pi)*(75*10**-6 
                                             + 1.868*10**-3*math.cos(b) 
                                             - 32.077*10**-3*math.sin(b) 
                                             - 14.615*10**-3*math.cos(2*b) 
                                             - 40.9*10**-3*math.sin(2*b))
            
            time_solar = t.hour + time_equation/60 - (15 - float(self.location.longitude))/15
            
            # Day light saving e.g. between 27. Mar, 02:00 and 30. Oct, 03:00 in central europe
            if (t.dst() != timedelta(0)):
                time_solar -= 1
            
            rad_hour = math.radians(15*(time_solar - 12))
            rad_latitude = math.radians(float(self.location.latitude))
            
            rad_declination = math.radians(23.45*np.sin((np.deg2rad(360*(284+day_of_year)/365))))
            rad_elevation = math.asin(math.sin(rad_latitude)*math.sin(rad_declination) 
                                        + (math.cos(rad_latitude)*math.cos(rad_declination)*math.cos(rad_hour)))
            
            if math.cos(rad_hour) < (math.tan(rad_declination)/math.tan(rad_latitude)):
                rad_azimuth = 2*math.pi + math.asin(-1*math.cos(rad_declination)*math.sin(rad_hour)/math.cos(rad_elevation))
            else:
                rad_azimuth = math.pi - math.asin(-1*math.cos(rad_declination)*math.sin(rad_hour)/math.cos(rad_elevation))
                
            if rad_azimuth > (2*math.pi):
                rad_azimuth -= 2*math.pi
            
            rad_tilt = math.radians(self.modules_param['tilt'])
            rad_orientation = math.radians(self.modules_param['orientation'])
            
            rad_incidence = math.acos(math.sin(rad_elevation)*math.cos(rad_tilt) 
                                        + math.cos(rad_elevation)*math.sin(rad_tilt)*math.cos(rad_orientation - rad_azimuth))
        
            row.incidence = math.degrees(rad_incidence)
            row.elevation = math.degrees(rad_elevation)
            row.zenith = math.degrees(math.pi/2 - rad_elevation)
            row.azimuth = math.degrees(rad_azimuth)
            
        return angles
    
        
    def _load_parameters(self, id):
        here = os.path.abspath(os.path.dirname(__file__))
        datadir = os.path.join(here, "data")
        if not os.path.exists(datadir):
            os.makedirs(datadir)
            
        paramfile = os.path.join(datadir, id.lower() + '.cfg')
        if (os.path.isfile(paramfile)):
            paramjson = open(paramfile)
            params = json.load(paramjson)
        else:
            paramfile_default = os.path.join(os.path.dirname(here), 'conf', 'systems_param.cfg')
            config = ConfigParser()
            config.read(paramfile_default)
            
            params = {}
            for (key, value) in config.items('Default'):
                params[key] = self._parse_parameter(value)
            
            params['eta'] = params['eta_dirt']*params['eta_field']*params['eta_inv']
            with open(paramfile, 'w') as paramjson:
                json.dump(params, paramjson)
            
        return params
    
    
    def _parse_parameter(self, parameter):
        try:
            return int(parameter)
        except ValueError:
            return float(parameter)
        