#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import os
import json
import datetime
import math
import numpy as np
import pandas as pd
import pvlib as pv


def read(filepath, timezone, method='csv'):
    if method == 'csv':
        forecast_csv = pd.read_csv(filepath, 
                                   usecols=['time','aswdifd_s','aswdir_s','t_2m','t_g'], 
                                   index_col='time', parse_dates=['time'])
        
        forecast_csv = forecast_csv.ix[:,:'t_2m'].rename(columns = {'aswdir_s':'direct', 'aswdifd_s':'diffuse', 't_2m':'temperature'})
        forecast_csv.index = forecast_csv.index.tz_localize('UTC').tz_convert(timezone)
        forecast_csv = np.absolute(forecast_csv)
        
        forecast = Forecast(os.path.basename(filepath).replace('.csv', ''), os.path.dirname(os.path.abspath(filepath)), 
                            forecast_csv.index, 
                            forecast_csv['direct']+forecast_csv['diffuse'], forecast_csv['diffuse'], forecast_csv['temperature'])
    
    return forecast


def latest(dir, key, timezone, method='csv'):
    forecastfile = None
    if method == 'csv':
        try:
            for file in os.listdir(dir):
                if (key + '_' in file) and (file.endswith('.csv')):
                    if (forecastfile == None) or (file[3:-4] > forecastfile[3:-4]):
                        forecastfile = file
        except IOError:
            print("Error: unable to read irradiance forecast file in \"{}\"".format(dir))
        else:
            if(forecastfile == None):
                raise IOError("Unable to find irradiance forecast files in \"{}\"".format(dir))
            else:
                return read(os.path.join(dir, forecastfile), timezone, method)


def get_filename(time, key, method='csv'):
    date = time.tz_convert('UTC')
    # Add daylight savings time offset, if necessary
    if time.dst() != datetime.timedelta(0):
        date = date + pd.DateOffset(seconds=time.dst().total_seconds())
    datestr = date.strftime('%Y%m%d%H')
    name = key + '_' + str(datestr) + '.csv'
    
    return name


class Forecast:
    def __init__(self, id, dir, times, global_horizontal, diffuse_horizontal, temperature):
        self.id = id
        self.dir = dir
        
        self.times = times
        self.global_horizontal = global_horizontal
        self.diffuse_horizontal = diffuse_horizontal
        self.temperature = temperature
    
    
    def irradiation(self, system):
        """ 
            Calculates the global irradiation on a tilted surface, consisting out of the sum of
            direct, diffuse and reflected irradiance components.
            
            :param system: The photovoltaic system, solar irradiation forecast on a horizontal surface.
            
        """
        timestamps = pd.date_range(self.times[0], self.times[-1] + pd.DateOffset(minutes=59), freq='min')
        pressure = pv.atmosphere.alt2pres(system.location.altitude)
        
        # Get the solar angles, determining the suns irradiation on a surface by an implementation of the NREL SPA algorithm
        angles = pv.solarposition.get_solarposition(timestamps, system.location, pressure=pressure)
        
        global_horizontal = self.global_horizontal.resample('1min', fill_method='ffill', kind='timestamp', how='last')
        diffuse_horizontal = self.diffuse_horizontal.resample('1min', fill_method='ffill', kind='timestamp', how='last')
        
        # Determine direct normal irradiance as defined by Quaschning
        direct_normal = (global_horizontal - diffuse_horizontal)*(1/np.sin(np.deg2rad(angles['elevation'])))
        direct_normal.loc[direct_normal <= 0] = 0
        
        direct = pv.irradiance.beam_component(system.modules_param['tilt'], system.modules_param['azimuth'], 
                                              angles['zenith'], angles['azimuth'], 
                                              direct_normal)
        
        # Determine extraterrestrial radiation and airmass
        extra = pv.irradiance.extraradiation(timestamps)
        airmass_rel = pv.atmosphere.relativeairmass(angles['apparent_zenith'])
        airmass = pv.atmosphere.absoluteairmass(airmass_rel, pressure)
        
        diffuse = pv.irradiance.perez(surface_tilt=system.modules_param['tilt'], surface_azimuth=system.modules_param['azimuth'], 
                                      solar_zenith=angles['apparent_zenith'], solar_azimuth=angles['azimuth'], 
                                      dhi=diffuse_horizontal, dni=direct_normal, dni_extra=extra, 
                                      airmass=airmass)
        
        reflected = pv.irradiance.grounddiffuse(surface_tilt=system.modules_param['tilt'], 
                                                ghi=global_horizontal, 
                                                albedo=system.modules_param['albedo'])
        
        # Calculate the total irradiation, using the perez model
#         irradation = pv.irradiance.total_irrad(surface_tilt=system.modules_param['tilt'], surface_azimuth=system.modules_param['azimuth'], 
#                                                solar_zenith=angles['apparent_zenith'], solar_azimuth=angles['azimuth'], 
#                                                dni=forecast['normal'], ghi=forecast['global'], dhi=forecast['diffuse'], 
#                                                dni_extra=extra, airmass=airmass, 
#                                                surface_type=system.modules_param['albedo'], 
#                                                model='perez')
        
        
        # Calculate total irradiation and replace values smaller than specific threshold
        # Check if still necessary, for better forecasts
        total = direct.fillna(0) + diffuse.fillna(0) + reflected.fillna(0)
        total_hourly = total.resample('1h', how='mean')
        total_hourly.loc[total_hourly < 0.01] = 0
        
        return pd.Series(total_hourly.fillna(0), name='irradiation')
