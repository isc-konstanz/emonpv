# -*- coding: utf-8 -*-
"""
    pvforecast.weather
    ~~~~~
    
    This module provides functions to read :class:`pvforecast.Weather` objects, 
    used as reference to calculate a photovoltaic installations' generated power.
    The provided environmental data contains temperatures and horizontal 
    solar irradiation, which can be used, to calculate the effective irradiance 
    on defined, tilted photovoltaic systems.
    
"""
import logging
logger = logging.getLogger('pvforecast.weather')

import os
import numpy as np
import pandas as pd
import pvlib as pv
import datetime


def forecast(date, timezone, longitude=None, latitude=None, var=None, method='DWD_CSV'):
    """ 
    Reads the predicted weather data for a specified location, retrieved through 
    several possible methods:
    
    - DWD_CSV:
        Reads an hourly interval of 23 hours from a csv file, parsed from data provided by
        the DWDs' (Deutscher Wetterdienst) Global Data Set ftp server, where a new data set 
        of the following 23 hours gets provided every 6 hours in GRIB2 format.
        The csv directory has to be specified with the 'var' parameter.
    
    
    :param date: 
        the date for which the closest possible weather forecast will be looked up for.
        For many applications, passing datetime.datetime.now() will suffice.
    :type date: 
        :class:`pandas.tslib.Timestamp` or datetime
    
    :param timezone: 
        See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
        valid time zones.
    :type timezone:
        str or unicode
    
    :param longitude: 
        the locations degree north of the equator in decimal degrees notation.
    :type longitude:
        float
    
    :param latitude: 
        the locations degree east of the prime meridian in decimal degrees notation.
    :type latitude:
        float
    
    :param method: 
        the defining method, how the weather data should be retrieved.
    :type method:
        str or unicode
    
    
    :returns: 
        the Weather object, containing the data columns 'global_horizontal' or 
        'direct_horizontal', 'diffuse_horizontal' and 'temperature', indexed by 
        timezone aware :class:`pandas.DatetimeIndex`.
    :rtype: 
        :class:`pvforecast.Weather`
    """
    if method.lower() == 'dwd_csv':
        csv = _get_dwdcsv_nearest(date, var)
        return _read_dwdcsv(csv, timezone)
        
    else:
        raise ValueError('Invalid irradiation forecast method "{}"'.method)


def reference(date, timezone, var=None, method='DWD_PUB'):
    """ 
    Reads historical weather data for a specified location, retrieved through 
    several possible methods:
    
    - DWD_PUB:
        Reads an hourly interval of 23 hours from a text file, provided by the DWDs' 
        (Deutscher Wetterdienst) public ftp server, where data will be updated roughly
        once a month.
        The DWD specific location key has to be specified with the 'var' parameter.
    
    
    :param date: 
        the date for which the closest possible weather forecast will be looked up for.
        For many applications, passing datetime.datetime.now() will suffice.
    :type date: 
        :class:`pandas.tslib.Timestamp` or datetime
    
    :param timezone: 
        See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
        valid time zones.
    :type timezone:
        str or unicode
    
    :param method: 
        the defining method, how the weather data should be retrieved.
    :type method:
        str or unicode
    
    
    :returns: 
        the Weather object, containing the data columns 'global_horizontal' or 
        'direct_horizontal', 'diffuse_horizontal' in W/m^2 and 'temperature' in 
        degree Celsius, indexed by timezone aware :class:`pandas.DatetimeIndex`.
    :rtype: 
        :class:`pvforecast.Weather`
    """
    if method.lower() == 'dwd_pub':
        return _read_dwdpublic(var, timezone)
    else:
        raise ValueError('Invalid irradiation reference method "{}"'.method)


# def _read_dwd_grib2():
    

def _read_dwdcsv(csvname, timezone):
    """
    Reads an hourly interval of 23 hours from a csv file, parsed from data provided by
    the DWDs' (Deutscher Wetterdienst) Global Data Set ftp server, where a new data set 
    of the following 23 hours gets provided every 6 hours in GRIB2 format.
    
    
    :param csvname: 
        the name of the csv file, containing the weather data.
    :type csvname:
        str or unicode
    
    :param timezone: 
        See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
        valid time zones.
    :type timezone:
        str or unicode
    
    
    :returns: 
        the Weather object, containing the data columns 'global_horizontal' or 
        'direct_horizontal', 'diffuse_horizontal' in W/m^2 and 'temperature' in 
        degree Celsius, indexed by timezone aware :class:`pandas.DatetimeIndex`.
    :rtype: 
        :class:`pvforecast.Weather`
    """
    csv = pd.read_csv(csvname, 
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
    result.key = os.path.basename(csvname).replace('.csv', '')
    return result


def _get_dwdcsv_nearest(date, path):
    """
    Retrieve the csv file closest to a passed date, following the file naming
    scheme "KEY_YYYYMMDDHH.csv"
    
    
    :param date: 
        the date for which the closest possible csv file will be looked up for.
    :type date: 
        :class:`pandas.tslib.Timestamp` or datetime
    
    :param path: 
        the directory, in which csv files should be looked up in.
    :type path:
        str or unicode
    
    
    :returns: 
        the full path and filename of the closest found csv file.
    :rtype: 
        str
    """
    
    if isinstance(date, pd.tslib.Timestamp):
        date = date.tz_convert('UTC')
    
    ref = int(date.strftime('%Y%m%d%H'))
    diff = 1970010100
    csv = None
    try:
        for f in os.listdir(path):
            if not '_yield' in f and f.endswith('.csv'):
                d = abs(ref - int(f[3:-4]))
                if (d < diff):
                    diff = d
                    csv = f
    except IOError:
        logger.error('Unable to read irradiance forecast file in "%s"', path)
    else:
        if(csv == None):
            raise IOError('Unable to find irradiance forecast files in "%s"', path)
        else:
            return os.path.join(path, csv)


def _read_dwdpublic(key, timezone):
    """
    Reads an hourly interval of 23 hours from a text file, provided by the DWDs' 
    (Deutscher Wetterdienst) public ftp server, where data will be updated roughly
    once a month.
    
    
    :param key: 
        the DWD specific location key. Information about possible locations can be found with:
        ftp://ftp-cdc.dwd.de/pub/CDC/observations_germany/climate/hourly/solar/ST_Beschreibung_Stationen.txt
    :type key:
        str or unicode
    
    :param timezone: 
        See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
        valid time zones.
    :type timezone:
        str or unicode
    
    
    :returns: 
        the Weather object, containing the data columns 'global_horizontal' or 
        'direct_horizontal', 'diffuse_horizontal' in W/m^2 and 'temperature' in 
        degree Celsius, indexed by timezone aware :class:`pandas.DatetimeIndex`.
    :rtype: 
        :class:`pvforecast.Weather`
    """
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
    """
    The Weather object provides horizontal solar irradiation and temperature
    data as a :class:`pandas.DataFrame`. It needs to contain specific columns, 
    to being able to calculate the total solar irradiation on a defined photovoltaic
    systems' tilted surface.
    
    A Weather DataFrame contains either the columns 'global_horizontal' or 
    'direct_horizontal', additional to 'diffuse_horizontal' and 'temperature'.
    Depending on which columns are available, :func:`calculate` will calculate
    the total irradiance on the passed photovoltaic systems' tilted surface in a 
    slightly adjusted matter.
    """
    _metadata = ['key']
 
    @property
    def _constructor(self):
        return Weather
    
    
    def calculate(self, system):
        """ 
        Calculates the total solar irradiation on a defined photovoltaic systems' 
        tilted surface, consisting out of the sum of direct, diffuse and reflected 
        irradiance components.
        
        :param system: 
            the photovoltaic system, defining the surface orientation and tilt to 
            calculate the irradiance for.
        :type system: 
            :class:`pvforecast.System`
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
