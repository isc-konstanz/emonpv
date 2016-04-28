#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import logging
logger = logging.getLogger('pvprediction')

import os
import numpy as np
import pandas as pd
import pvlib as pv
import datetime


def forecast(date, timezone, longitude=None, latitude=None, var=None, method='DWD'):
    if method == 'DWD_CSV':
        csv = _get_dwdcsv_nearest(date, var)
        return _read_dwdcsv(csv, date, timezone)
        
    else:
        raise ValueError('Invalid irradiation forecast method "{}"'.method)


def reference(date, timezone, longitude, latitude, key=None, method='DWD'):
    if method == 'DWD':
        from urllib import urlopen
        from zipfile import ZipFile
        from StringIO import StringIO
        
        url = urlopen('ftp://ftp-cdc.dwd.de/pub/CDC/observations_germany/climate/hourly/solar/stundenwerte_ST_' + key + '.zip')
        zipfile = ZipFile(StringIO(url.read()))
        
        irradiation_csv = pd.read_csv(zipfile.open('produkt_strahlung_Stundenwerte_19770101_20160229_' + key + '.txt'),
                                      usecols=[' MESS_DATUM','DIFFUS_HIMMEL_KW_J','GLOBAL_KW_J'],
                                      index_col=' MESS_DATUM', parse_dates=[' MESS_DATUM'])
        print(irradiation_csv)
        
    else:
        raise ValueError('Invalid irradiation reference method "{}"'.method)


# def _read_dwd_grib2():
    

def _read_dwdcsv(path, date, timezone):
    csv = pd.read_csv(path, 
                      usecols=['time','aswdifd_s','aswdir_s','t_2m','t_g'], 
                      index_col='time', parse_dates=['time'])
        
    csv = csv.ix[:,:'t_2m'].rename(columns = {'aswdir_s':'direct', 'aswdifd_s':'diffuse', 't_2m':'temperature'})
    csv.index = csv.index.tz_localize('UTC').tz_convert(timezone)
    csv = np.absolute(csv)
    
    forecast = Irradiation(os.path.basename(path).replace('.csv', ''), 
                           csv.index, 
                           csv['direct']+csv['diffuse'], csv['diffuse'], csv['temperature'])
    
    return forecast


def _get_dwdcsv_nearest(date, path):
    cswdir = os.path.dirname(path)
    dwdkey = os.path.basename(path)
    
    ref = int(date.strftime('%Y%m%d%H'))
    diff = 1970010100
    csv = None
    try:
        for f in os.listdir(cswdir):
            if (dwdkey + '_' in f) and (f.endswith('.csv')):
                d = abs(ref - int(f[3:-4]))
                if (d < diff):
                    diff = d
                    csv = f
    except IOError:
        logger.error('Unable to read irradiance forecast file in "%s"', format(dir))
    else:
        if(csv == None):
            raise IOError("Unable to find irradiance forecast files in \"{}\"".format(dir))
        else:
            return os.path.join(cswdir, csv)
            

def _get_dwdcsv(date, path):
    date = date.tz_convert('UTC')
    # Add daylight savings time offset, if necessary
    if date.dst() != datetime.timedelta(0):
        date = date + pd.DateOffset(seconds=date.dst().total_seconds())
    datestr = date.strftime('%Y%m%d%H')
    
    return path + '_' + str(datestr) + '.csv'


class Irradiation:
    def __init__(self, key, times, global_horizontal, diffuse_horizontal, temperature):
        self.id = key
        
        self.times = times
        self.global_horizontal = global_horizontal
        self.diffuse_horizontal = diffuse_horizontal
        self.temperature = temperature
    
    
    def calculate(self, system):
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
