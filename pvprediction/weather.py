#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
import logging
logger = logging.getLogger('pvprediction.weather')

import os
import numpy as np
import pandas as pd
import pvlib as pv
import datetime


def forecast(date, timezone, longitude=None, latitude=None, var=None, method='DWD'):
    if method == 'DWD_CSV':
        csv = _get_dwdcsv_nearest(date, var)
        return _read_dwdcsv(csv, timezone)
        
    else:
        raise ValueError('Invalid irradiation forecast method "{}"'.method)


def reference(date, timezone, longitude=None, latitude=None, var=None, method='DWD'):
    if method == 'DWD_PUB':
        return _read_dwdpublic(var, timezone)
    else:
        raise ValueError('Invalid irradiation reference method "{}"'.method)


# def _read_dwd_grib2():
    

def _read_dwdcsv(path, timezone):
    csv = pd.read_csv(path, 
                      usecols=['time','aswdifd_s','aswdir_s','t_2m','t_g'], 
                      index_col='time', parse_dates=['time'])
        
    csv = csv.ix[:,:'t_2m'].rename(columns = {'aswdir_s':'direct_horizontal', 'aswdifd_s':'diffuse_horizontal', 't_2m':'temperature'})
    csv.index.name = 'time'
    
    if not csv.empty:
        csv.index = csv.index.tz_localize('UTC').tz_convert(timezone)
        
        csv = np.absolute(csv)
        
        # Convert the ambient temperature from Kelvin to Celsius
        csv['temperature'] = csv['temperature'] - 273.15
    
    result = Weather(csv)
    result.key = os.path.basename(path).replace('.csv', '')
    return result


def _get_dwdcsv_nearest(date, path):
    cswdir = os.path.dirname(path)
    dwdkey = os.path.basename(path)
    
    if isinstance(date, pd.tslib.Timestamp):
        date = date.tz_convert('UTC')
    
    ref = int(date.strftime('%Y%m%d%H'))
    diff = 1970010100
    csv = None
    try:
        for f in os.listdir(cswdir):
            if dwdkey + '_' in f and not '_yield' in f and f.endswith('.csv'):
                d = abs(ref - int(f[3:-4]))
                if (d < diff):
                    diff = d
                    csv = f
    except IOError:
        logger.error('Unable to read irradiance forecast file in "%s"', cswdir)
    else:
        if(csv == None):
            raise IOError('Unable to find irradiance forecast files in "%s"', cswdir)
        else:
            return os.path.join(cswdir, csv)


def _get_dwdcsv(date, path):
    date = date.tz_convert('UTC')
    # Add daylight savings time offset, if necessary
    if date.dst() != datetime.timedelta(0):
        date = date + pd.DateOffset(seconds=date.dst().total_seconds())
    datestr = date.strftime('%Y%m%d%H')
    
    return path + '_' + str(datestr) + '.csv'


def _read_dwdpublic(key, timezone):
    from urllib import urlopen
    from zipfile import ZipFile
    from StringIO import StringIO
    
    # Retrieve measured temperature values from DWD public ftp server
    url = urlopen('ftp://ftp-cdc.dwd.de/pub/CDC/observations_germany/climate/hourly/air_temperature/recent/stundenwerte_TU_' + key + '_akt.zip')
    zipfile = ZipFile(StringIO(url.read()))
    for f in zipfile.namelist():
        if ('produkt_temp_Terminwerte_' in f):
            temp = pd.read_csv(zipfile.open(f), sep=";",
                                        usecols=[' MESS_DATUM',' LUFTTEMPERATUR'])
    temp.index = pd.to_datetime(temp[' MESS_DATUM'], format="%Y%m%d%H")
    temp.index = temp.index.tz_localize('UTC').tz_convert(timezone)
    temp.index.name = 'time'
    temp = temp.rename(columns = {' LUFTTEMPERATUR':'temperature'})
    
    # Missing values get identified with "-999"
    temp = temp.replace('-999', np.nan)
    
    
    # Retrieve measured solar irradiation observations from DWD public ftp server
    url = urlopen('ftp://ftp-cdc.dwd.de/pub/CDC/observations_germany/climate/hourly/solar/stundenwerte_ST_' + key + '.zip')
    zipfile = ZipFile(StringIO(url.read()))
    for f in zipfile.namelist():
        if ('produkt_strahlung_Stundenwerte_' in f):
            irr = pd.read_csv(zipfile.open(f), sep=";",
                                        usecols=[' MESS_DATUM','DIFFUS_HIMMEL_KW_J','GLOBAL_KW_J'])
    
    irr.index = pd.to_datetime(irr[' MESS_DATUM'], format="%Y%m%d%H:%M")
    irr.index = irr.index.tz_localize('UTC').tz_convert(timezone)
    irr.index.name = 'time'
    
    # Shift index by 30 min, to move from interval center values to hourly averages
    irr.index = irr.index - datetime.timedelta(minutes=30)
    
    # Missing values get identified with "-999"
    irr = irr.replace('-999', np.nan)
    
    # Global and diffuse irradiation unit transformation from hourly J/cm^2 to mean W/m^2
    irr['global_horizontal'] = irr['GLOBAL_KW_J']*(100**2)/3600
    irr['diffuse_horizontal'] = irr['DIFFUS_HIMMEL_KW_J']*(100**2)/3600
    
    reference = pd.concat([irr['global_horizontal'], irr['diffuse_horizontal'], temp['temperature']], axis=1)
    # Drop rows without either solar irradiation or temperature values
    reference = reference[(reference.index >= temp.index[0]) & (reference.index >= irr.index[0]) & 
                          (reference.index <= temp.index[-1]) & (reference.index <= irr.index[-1])]
    
    result = Weather(reference)
    result.key = key
    return result

    
class Weather(pd.DataFrame):
    _metadata = ['key']
 
    @property
    def _constructor(self):
        return Weather
    
    
    def calculate(self, system):
        """ 
            Calculates the global irradiation on a tilted surface, consisting out of the sum of
            direct, diffuse and reflected irradiance components.
            
            :param system: The photovoltaic system, solar irradiation forecast on a horizontal surface.
            
        """
        timestamps = pd.date_range(self.index[0], self.index[-1] + pd.DateOffset(minutes=59), freq='min').tz_convert('UTC')
        pressure = pv.atmosphere.alt2pres(system.location.altitude)
        
        dhi = self.diffuse_horizontal.resample('1min', kind='timestamp').last().ffill()
        dhi.index = dhi.index.tz_convert('UTC')
            
        if 'global_horizontal' in self.columns:
            ghi = self.global_horizontal.resample('1min', kind='timestamp').last().ffill()
        else:
            ghi = self.direct_horizontal.resample('1min', kind='timestamp').last().ffill() + dhi
        ghi.index = ghi.index.tz_convert('UTC')
        
        # Get the solar angles, determining the suns irradiation on a surface by an implementation of the NREL SPA algorithm
        angles = pv.solarposition.get_solarposition(timestamps, system.location.latitude, system.location.longitude, altitude=system.location.altitude, pressure=pressure)
        
        if 'global_horizontal' in self.columns:
            zenith = angles['apparent_zenith'].copy()
            zenith[angles['apparent_zenith'] > 87] = np.NaN
            zenith = zenith.dropna(axis=0)
            dni = pv.irradiance.dirint(ghi[zenith.index], zenith, zenith.index, pressure=pressure)
            dni = pd.Series(dni, index=timestamps).fillna(0)
        else:
            # Determine direct normal irradiance as defined by Quaschning
            dni = ((ghi - dhi)*(1/np.sin(np.deg2rad(angles['elevation'])))).fillna(0)
            dni.loc[dni <= 0] = 0
          
        # Determine extraterrestrial radiation and airmass
        extra = pv.irradiance.extraradiation(timestamps)
        airmass_rel = pv.atmosphere.relativeairmass(angles['apparent_zenith'])
        airmass = pv.atmosphere.absoluteairmass(airmass_rel, pressure)
        
        # Calculate the total irradiation, using the perez model
        irradiation = pv.irradiance.total_irrad(system.modules_param['tilt'], system.modules_param['azimuth'], 
                                                angles['apparent_zenith'], angles['azimuth'], 
                                                dni, ghi, dhi, 
                                                dni_extra=extra, airmass=airmass, 
                                                albedo=system.modules_param['albedo'], 
                                                model='perez')
        
#         direct = pv.irradiance.beam_component(system.modules_param['tilt'], system.modules_param['azimuth'], 
#                                               angles['zenith'], angles['azimuth'], 
#                                               dni)
#         
#         diffuse = pv.irradiance.perez(surface_tilt=system.modules_param['tilt'], surface_azimuth=system.modules_param['azimuth'], 
#                                       solar_zenith=angles['apparent_zenith'], solar_azimuth=angles['azimuth'], 
#                                       dhi=dhi, dni=dni, dni_extra=extra, 
#                                       airmass=airmass)
#          
#         reflected = pv.irradiance.grounddiffuse(surface_tilt=system.modules_param['tilt'], 
#                                                 ghi=ghi, 
#                                                 albedo=system.modules_param['albedo'])
        
        # Calculate total irradiation and replace values smaller than specific threshold
        # Check if still necessary, for better forecasts
        total = irradiation['poa_global'].fillna(0)
#         total = direct.fillna(0) + diffuse.fillna(0) + reflected.fillna(0)
        total_hourly = total.resample('1h').mean()
        total_hourly.loc[total_hourly < 0.01] = 0
        total_hourly.index = total_hourly.index.tz_convert(system.location.tz)
        
        return pd.Series(total_hourly, name='irradiation')
