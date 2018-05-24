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
from pvlib.forecast import ForecastModel
import requests
import json


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
    elif method.lower() == 'cosmo_de':
        return _read_cosmo_de(date, timezone, longitude, latitude)
    elif method.lower() == 'icon_eu':
        return _read_icon_eu(date, timezone, longitude, latitude)
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


def check_update(date, timezone, longitude, latitude, method='COSMO_DE'):
    #date = pd.Timestamp(date).tz_localize('UTC').tz_convert(timezone)
    if method.lower() == 'dwd_csv':
        return (True, None)
    elif method.lower() == 'cosmo_de':
        return COSMO_DE().is_new(latitude, longitude, date)
    elif method.lower() == 'icon_eu':
        return ICON_EU().is_new(latitude, longitude, date)
    else:
        raise ValueError('Invalid forecast method "{}"'.method)

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
    from urllib import request
    from zipfile import ZipFile
    from io import BytesIO
    
    # Retrieve measured temperature values from DWD public ftp server
    url = request.urlopen('ftp://ftp-cdc.dwd.de/pub/CDC/observations_germany/climate/hourly/air_temperature/recent/stundenwerte_TU_' + key + '_akt.zip')
    zipfile = ZipFile(BytesIO(url.read()))
    for f in zipfile.namelist():
        if ('produkt_tu_stunde_' in f):
            temp = pd.read_csv(zipfile.open(f), sep=";",
                                        usecols=['MESS_DATUM','TT_TU'])
    temp.index = pd.to_datetime(temp['MESS_DATUM'], format="%Y%m%d%H")
    temp.index = temp.index.tz_localize('UTC').tz_convert(timezone)
    temp.index.name = 'time'
    temp = temp.rename(columns = {'TT_TU':'temperature'})
    
    # Missing values get identified with "-999"
    temp = temp.replace('-999', np.nan)
    
    
    # Retrieve measured solar irradiation observations from DWD public ftp server
    url = request.urlopen('ftp://ftp-cdc.dwd.de/pub/CDC/observations_germany/climate/hourly/solar/stundenwerte_ST_' + key + '_row.zip')
    zipfile = ZipFile(BytesIO(url.read()))
    for f in zipfile.namelist():
        if ('produkt_st_stunde_' in f):
            irr = pd.read_csv(zipfile.open(f), sep=";",
                                        usecols=['MESS_DATUM','FD_LBERG','FG_LBERG'])
    
    irr.index = pd.to_datetime(irr['MESS_DATUM'], format="%Y%m%d%H:%M")
    irr.index = irr.index.tz_localize('UTC').tz_convert(timezone)
    irr.index.name = 'time'
    
    # Shift index by 30 min, to move from interval center values to hourly averages
    irr.index = irr.index - datetime.timedelta(minutes=30)
    
    # Missing values get identified with "-999"
    irr = irr.replace('-999', np.nan)
    
    # Global and diffuse irradiation unit transformation from hourly J/cm^2 to mean W/m^2
    irr['global_horizontal'] = irr['FG_LBERG']*(100**2)/3600
    irr['diffuse_horizontal'] = irr['FD_LBERG']*(100**2)/3600
    
    reference = pd.concat([irr['global_horizontal'], irr['diffuse_horizontal'], temp['temperature']], axis=1)
    # Drop rows without either solar irradiation or temperature values
    reference = reference[(reference.index >= temp.index[0]) & (reference.index >= irr.index[0]) & 
                          (reference.index <= temp.index[-1]) & (reference.index <= irr.index[-1])]
    
    result = Weather(reference)
    result.key = key
    return result


def _read_cosmo_de(date, timezone, longitude, latitude):
    date = pd.Timestamp(date).tz_localize('UTC').tz_convert(timezone)
    return COSMO_DE().get_processed_data(latitude, longitude, date, None)#start + pd.Timedelta(days=7)

def _read_icon_eu(date, timezone, longitude, latitude):
    date = pd.Timestamp(date).tz_localize('UTC').tz_convert(timezone)
    return ICON_EU().get_processed_data(latitude, longitude, date, None)#start + pd.Timedelta(days=7)
    
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


        #kappa = 1.041
        #z = np.radians(angles['apparent_zenith'])
        #eps = ((dhi + dni) / dhi + kappa * (z ** 3)) / (1 + kappa * (z ** 3))
        #print(eps)
        
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

def convertDate(date):
    return pd.to_datetime(date.replace('T', ' '))

class COSMO_DE(ForecastModel):
    """
    Subclass of the ForecastModel class representing COSMO-DE
    forecast model.

    Model data corresponds to 2.8km resolution forecasts.

    Parameters
    ----------
    set_type: string, default 'best'
        Type of model to pull data from.

    Attributes
    ----------
    dataframe_variables: list
        Common variables present in the final set of data.
    model: string
        Name of the UNIDATA forecast model.
    model_type: string
        UNIDATA category in which the model is located.
    variables: dict
        Defines the variables to obtain from the weather
        model and how they should be renamed to common variable names.
    units: dict
        Dictionary containing the units of the standard variables
        and the model specific variables.
    """

    def __init__(self, set_type='best'):
        model_type = 'Forecast Model Data'

        model = 'COSMO-DE Forecast'

        self.variables = {
            "high_clouds": "Bedeckungsgrad mit hohen Wolken [%]",
            "longwave_sfc": "langwellige Strahlungsbilanz a d Oberfl [W/m^2]",
            "longwave_toa": "langwellige Strahlungsbilanz am Modelloberrand [W/m^2]",
            "low_clouds": "Bedeckungsgrad mit niedrigen Wolken [%]",
            "maxwindspeed10m": "max Windgeschwindigkeit in 10m Hoehe (Boeen) [m/s]",
            "mid_clouds": "Bedeckungsgrad mit mittleren Wolken [%]",
            "pressure_msl": "Luftdruck auf Meeresh\u00f6he [Pa]",
            "relative_humidity": "rel. Luftfeuchtigkeit auf 2m [%]",
            "shortwave_diffuse_downwards": "diffuse, abwaerts gerichtete kurzwellige Strahlung a d Oberfl [W/m^2]",
            "shortwave_diffuse_upwards": "diffuse, aufwaerts gerichtete kurzwellige Strahlung a d Oberfl [W/m^2]",
            "shortwave_direct": "direkte kurzwellige Strahlung a d Oberfl [W/m^2]",
            "shortwave_sfc": "kurzwellige Strahlungsbilanz a d Oberfl [W/m^2]",
            "shortwave_toa": "kurzwellige Strahlungsbilanz am Modelloberrand [W/m^2]",
            "t2m": "2m Temperatur [C]",
            "total_clouds": "Gesamtbedeckungsgrad mit Wolken [%]",
            "winddirection10m": "Windrichtung [Grad]",
            "windspeed10m": "Windgeschwindigkeit in 10m Hoehe [m/s]", }

        self.output_variables = [
            'temp_air',
            'wind_speed',
            'ghi',
            'dni',
            'dhi',
            'total_clouds',
            'low_clouds',
            'mid_clouds',
            'high_clouds']

        super(COSMO_DE, self).__init__(model_type, model, set_type)

    def process_data(self, data, cloud_cover='total_clouds', **kwargs):
        """
        Defines the steps needed to convert raw forecast data
        into processed forecast data.

        Parameters
        ----------
        data: DataFrame
            Raw forecast data
        cloud_cover: str, default 'total_clouds'
            The type of cloud cover used to infer the irradiance.

        Returns
        -------
        data: DataFrame
            Processed forecast data.
        """
        data = super(COSMO_DE, self).process_data(data, **kwargs)
        data['temp_air'] = data['t2m']
        data['wind_speed'] = data['windspeed10m']
        irrads = self.cloud_cover_to_irradiance(data[cloud_cover], **kwargs)
        data = data.join(irrads, how='outer')
        return data[self.output_variables]
    
    def get_data(self, latitude, longitude, start, end,
                 vert_level=None, query_variables=None,
                 close_netcdf_data=True):
        """
        Submits a query to the UNIDATA servers using Siphon NCSS and
        converts the netcdf data to a pandas DataFrame.

        Parameters
        ----------
        latitude: float
            The latitude value.
        longitude: float
            The longitude value.
        start: datetime or timestamp
            The start time.
        end: datetime or timestamp
            The end time.
        vert_level: None, float or integer, default None
            Vertical altitude of interest.
        query_variables: None or list, default None
            If None, uses self.variables.
        close_netcdf_data: bool, default True
            Controls if the temporary netcdf data file should be closed.
            Set to False to access the raw data.

        Returns
        -------
        forecast_data : DataFrame
            column names are the weather model's variable names.
        """
        self.latitude = latitude
        self.longitude = longitude
        self.set_location(start, latitude, longitude)

        self.start = start
        self.end = end

        url = 'http://52.30.78.76/solar/'+str(longitude)+'/'+str(latitude)
        r = json.loads(requests.get(url, headers={'Authorization': 'Basic aXNjOkxlZWc5YWh0aG8='}).text)

        cols = list(dict(r['timesteps'][0]['models']['COSMO_DE']).keys())
        vals = [[y[w] for w in cols] for y in [x["models"]['COSMO_DE'] for x in r['timesteps']]]
        
        self.data = pd.DataFrame(vals, columns=cols)
        self.data['date'] = self.data['date'].apply(convertDate)
        self.data = self.data.set_index('date')

        if pd.Timestamp.now() - pd.to_datetime(r['meta']['COSMO_DE']['run']) < pd.Timedelta(3, unit='h'):
            self.data.to_csv(str(longitude)+'_'+str(latitude)+'_cosmo_de_'+r['meta']['COSMO_DE']['run'].replace(':', '_')+'.csv', sep=',', encoding='utf-8')
            
        return self.data
    
    def is_new(self, latitude, longitude, date):
        url = 'http://52.30.78.76/solar/'+str(longitude)+'/'+str(latitude)
        r = json.loads(requests.get(url, headers={'Authorization': 'Basic aXNjOkxlZWc5YWh0aG8='}).text)
        return (pd.Timestamp(date) - pd.to_datetime(r['meta']['COSMO_DE']['run']) < pd.Timedelta(3, unit='h'), pd.to_datetime(r['meta']['COSMO_DE']['run']))

class ICON_EU(ForecastModel):
    """
    Subclass of the ForecastModel class representing ICON-EU
    forecast model.

    Model data corresponds to 6.5km resolution forecasts.

    Parameters
    ----------
    set_type: string, default 'best'
        Type of model to pull data from.

    Attributes
    ----------
    dataframe_variables: list
        Common variables present in the final set of data.
    model: string
        Name of the UNIDATA forecast model.
    model_type: string
        UNIDATA category in which the model is located.
    variables: dict
        Defines the variables to obtain from the weather
        model and how they should be renamed to common variable names.
    units: dict
        Dictionary containing the units of the standard variables
        and the model specific variables.
    """

    def __init__(self, set_type='best'):
        model_type = 'Forecast Model Data'

        model = 'ICON-EU Forecast'

        self.variables = {
            "high_clouds": "Bedeckungsgrad mit hohen Wolken [%]",
            "longwave_sfc": "langwellige Strahlungsbilanz a d Oberfl [W/m^2]",
            "longwave_toa": "langwellige Strahlungsbilanz am Modelloberrand [W/m^2]",
            "low_clouds": "Bedeckungsgrad mit niedrigen Wolken [%]",
            "maxwindspeed10m": "max Windgeschwindigkeit in 10m Hoehe (Boeen) [m/s]",
            "mid_clouds": "Bedeckungsgrad mit mittleren Wolken [%]",
            "pressure_msl": "Luftdruck auf Meeresh\u00f6he [Pa]",
            "relative_humidity": "rel. Luftfeuchtigkeit auf 2m [%]",
            "shortwave_diffuse_downwards": "diffuse, abwaerts gerichtete kurzwellige Strahlung a d Oberfl [W/m^2]",
            "shortwave_diffuse_upwards": "diffuse, aufwaerts gerichtete kurzwellige Strahlung a d Oberfl [W/m^2]",
            "shortwave_direct": "direkte kurzwellige Strahlung a d Oberfl [W/m^2]",
            "shortwave_sfc": "kurzwellige Strahlungsbilanz a d Oberfl [W/m^2]",
            "shortwave_toa": "kurzwellige Strahlungsbilanz am Modelloberrand [W/m^2]",
            "t2m": "2m Temperatur [C]",
            "total_clouds": "Gesamtbedeckungsgrad mit Wolken [%]",
            "winddirection10m": "Windrichtung [Grad]",
            "windspeed10m": "Windgeschwindigkeit in 10m Hoehe [m/s]", }

        self.output_variables = [
            'temp_air',
            'wind_speed',
            'ghi',
            'dni',
            'dhi',
            'total_clouds',
            'low_clouds',
            'mid_clouds',
            'high_clouds']

        super(ICON_EU, self).__init__(model_type, model, set_type)

    def process_data(self, data, cloud_cover='total_clouds', **kwargs):
        """
        Defines the steps needed to convert raw forecast data
        into processed forecast data.

        Parameters
        ----------
        data: DataFrame
            Raw forecast data
        cloud_cover: str, default 'total_clouds'
            The type of cloud cover used to infer the irradiance.

        Returns
        -------
        data: DataFrame
            Processed forecast data.
        """
        data = super(ICON_EU, self).process_data(data, **kwargs)
        data['temp_air'] = data['t2m']
        data['wind_speed'] = data['windspeed10m']
        #data['ghi'] = data['windspeed10m']
        #data['dni'] = data['windspeed10m']
        #data['dhi'] = data['windspeed10m']
        irrads = self.cloud_cover_to_irradiance(data[cloud_cover], **kwargs)
        data = data.join(irrads, how='outer')
        return data[self.output_variables]
    
    def get_data(self, latitude, longitude, start, end,
                 vert_level=None, query_variables=None,
                 close_netcdf_data=True):
        """
        Submits a query to the UNIDATA servers using Siphon NCSS and
        converts the netcdf data to a pandas DataFrame.

        Parameters
        ----------
        latitude: float
            The latitude value.
        longitude: float
            The longitude value.
        start: datetime or timestamp
            The start time.
        end: datetime or timestamp
            The end time.
        vert_level: None, float or integer, default None
            Vertical altitude of interest.
        query_variables: None or list, default None
            If None, uses self.variables.
        close_netcdf_data: bool, default True
            Controls if the temporary netcdf data file should be closed.
            Set to False to access the raw data.

        Returns
        -------
        forecast_data : DataFrame
            column names are the weather model's variable names.
        """
        self.latitude = latitude
        self.longitude = longitude
        self.set_location(start, latitude, longitude)

        self.start = start
        self.end = end
        
        #Wetterdaten vom Server holen!
        url = 'http://52.30.78.76/solar/'+str(longitude)+'/'+str(latitude)
        r = json.loads(requests.get(url, headers={'Authorization': 'Basic aXNjOkxlZWc5YWh0aG8='}).text)
        i = list(dict(r['timesteps'][0]['models']['ICON_EU']).keys())
        c = [[z[w] for w in i] for z in [x["models"]['ICON_EU'] for x in r['timesteps']]]
        
        self.data = pd.DataFrame(c, columns=i)
        self.data['date'] = self.data['date'].apply(convertDate)
        self.data = self.data.set_index('date')
        #pd.DataFrame(index=[], columns=self.variables).fillna(0)
        return self.data
    
    def is_new(self, latitude, longitude, date):
        url = 'http://52.30.78.76/solar/'+str(longitude)+'/'+str(latitude)
        r = json.loads(requests.get(url, headers={'Authorization': 'Basic aXNjOkxlZWc5YWh0aG8='}).text)
        return (pd.Timestamp(date) - pd.to_datetime(r['meta']['ICON_EU']['run']) < pd.Timedelta(3, unit='h'), pd.to_datetime(r['meta']['ICON_EU']['run']))