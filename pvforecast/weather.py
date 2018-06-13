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

import warnings
import requests
import json

import pandas as pd
import pytz as tz

from io import StringIO

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pvlib.forecast import ForecastModel


class Weather():
    
    def __init__(self, configs, database, model='NMM'):
        self.model = model
        if model == 'NMM':
            self.server = NMM(configs.get('Meteoblue', 'name'), 
                              configs.get('Meteoblue', 'address'), 
                              configs.get('Meteoblue', 'apikey'))
        elif model == 'COSMO_DE':
            self.server = COSMO_DE(configs.get('W3Data', 'address'), 
                                   configs.get('W3Data', 'apikey'))
        else:
            raise ValueError('Invalid forecast model argument')
        
        if 'csv' in database:
            self.database = database['csv']
        else:
            self.database = None


    def forecast(self, system, time):
        if self.database.exists(system, time):
            forecast = self.database.get(system, time)
        else:
            forecast = self.server.get_processed_data(system.location)
            
            # Store the retrieved forecast
            self.database.post(system, forecast, date=time)
        
        return forecast


class NMM(ForecastModel):
    """
    Subclass of the ForecastModel class representing the Meteoblue
    NMM (Nonhydrostatic Meso-Scale Modelling) forecast model.

    Model data corresponds to 4km resolution forecasts.

    Parameters
    ----------
    set_type: string, default 'best'
        Type of model to pull data from.

    Attributes
    ----------
    dataframe_variables: list
        Common variables present in the final set of data.
    model_name: string
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

    def __init__(self, name, address, apikey, set_type='best'):
        model_type = 'Forecast Model Data'
        model_name = 'NMM Forecast'

        self.variables = {
            "time": "Zeitpunkt [ISO8601]", 
            "precipitation": "Niederschlagsmenge [mm]", 
            "snowfraction": "Schneefall [0.0 - 1.0]", 
            "rainspot": "Regionale Übersicht für den Niederschlag", 
            "temperature": "Temperatur [C]", 
            "felttemperature": "gefühlte Temperatur [C]", 
            "pictocode": "Piktogrammcode", 
            "windspeed": "Windgeschwindigkeit [m/s]", 
            "winddirection": "Windrichtung [Grad]", 
            "relativehumidity": "relative luftfeuchtigkeit [%]", 
            "sealevelpressure": "Luftdruck auf Hoehe des Meerespiegels [hPa]", 
            "precipitation_probability": "Niederschlagswahrscheinlichkeit [%]", 
            "convective_precipitation": "Niederschlag als Schauer [mm]", 
            "isdaylight": "bei Tageslicht", 
            "sunshinetime": "Sonnenscheindauer [min]", 
            "lowclouds": "Bedeckungsgrad mit niedrigen Wolken [%]", 
            "midclouds": "Bedeckungsgrad mit mittleren Wolken [%]", 
            "highclouds": "Bedeckungsgrad mit hohen Wolken [%]", 
            "visibility": "Sichtweite [km]", 
            "totalcloudcover": "Gesamtbedeckungsgrad mit Wolken [%]", 
            "gni_instant": "", 
            "gni_backwards": "", 
            "dni_instant": "", 
            "dni_backwards": "", 
            "dif_instant": "", 
            "dif_backwards": "", 
            "ghi_instant": "", 
            "ghi_backwards": "", 
            "extraterrestrialradiation_instant": "", 
            "extraterrestrialradiation_backwards": ""
        }

        self.output_variables = [
            'temp_air',
            'wind_speed',
            'wind_direction',
            'humidity_rel',
            'pressure_sea',
            'ghi',
            'dni',
            'dhi',
            'total_clouds',
            'low_clouds',
            'mid_clouds',
            'high_clouds',
            'rain',
            'rain_shower',
            'rain_prob',
            'snow']
        
        self.name = name
        self.address = address
        self.apikey = apikey
        
        super(NMM, self).__init__(model_type, model_name, set_type)


    def process_data(self, data, **kwargs):
        """
        Defines the steps needed to convert raw forecast data
        into processed forecast data.

        Parameters
        ----------
        data: DataFrame
            Raw forecast data

        Returns
        -------
        data: DataFrame
            Processed forecast data.
        """
        data = super(NMM, self).process_data(data, **kwargs)
        
        data['temp_air'] = data['temperature']
        data['wind_speed'] = data['windspeed']
        data['wind_direction'] = data['winddirection']
        data['humidity_rel'] = data['relativehumidity']
        data['pressure_sea'] = data['sealevelpressure']
        data['ghi'] = data['ghi_instant']
        data['dni'] = data['dni_instant']
        data['dhi'] = data['dif_instant']
        data['total_clouds'] = data['totalcloudcover']
        data['low_clouds'] = data['lowclouds']
        data['mid_clouds'] = data['midclouds']
        data['high_clouds'] = data['highclouds']
        data['rain'] = data['precipitation']
        data['rain_shower'] = data['convective_precipitation']
        data['rain_prob'] = data['precipitation_probability']
        data['snow'] = data['snowfraction']
        
        return data[self.output_variables]


    def get_data(self, location):
        """
        Submits a query to the meteoblue servers and
        converts the CSV response to a pandas DataFrame.

        Parameters
        ----------
        location: Location
            The geographic location of the requested forecast data.

        Returns
        -------
        data : DataFrame
            column names are the weather model's variable names.
        """
        self.latitude = location.latitude
        self.longitude = location.longitude
        self.altitude = location.altitude
        self.location = location
        
        parameters = {
            'name': self.name,
            'tz': location.tz,
            'lat': location.latitude,
            'lon': location.longitude,
            'asl': location.altitude,
            'temperature': 'C',
            'windspeed': 'ms-1',
            'winddirection': 'degree',
            'precipitationamount': 'mm',
            'timeformat': 'iso8601',
            'format': 'csv',
            'apikey': self.apikey
        }
        response = requests.get(self.address + 'packages/basic-1h_clouds-1h_solar-1h', params=parameters)
        
        if response.status_code != 200:
            raise requests.HTTPError("Response returned with error " + response.status_code + ": " + response.reason)
        
        self.data = pd.read_csv(StringIO(response.text), sep=',')
        self.data['time'] = pd.to_datetime(self.data['time'])
        self.data = self.data.set_index('time')
        self.data = self.data.tz_localize(tz.utc).tz_convert(location.tz)
        
        return self.data


    def get_meta(self, location):
        parameters = {
            'name': self.name,
            'tz': location.tz,
            'lat': location.latitude,
            'lon': location.longitude,
            'asl': location.altitude,
            'timeformat': 'iso8601',
            'format': 'json',
            'apikey': self.apikey
        }
        response = requests.get(self.address + 'packages/basic-1h_clouds-1h_solar-1h', params=parameters)
        
        if response.status_code != 200:
            raise requests.HTTPError("Response returned with error " + response.status_code + ": " + response.reason)
        
        data = json.loads(response.text)
        return data.get('metadata')


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
    model_name: string
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

    def __init__(self, address, api_key, set_type='best'):
        model_type = 'Forecast Model Data'
        model_name = 'COSMO-DE Forecast'
        
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
        
        self.address = address
        self.apikey = api_key
        
        super(COSMO_DE, self).__init__(model_type, model_name, set_type)


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


    def get_data(self, location):
        """
        Submits a query to the W3 Data GmbH servers and
        converts the JSON response to a pandas DataFrame.

        Parameters
        ----------
        location: Location
            The geographic location of the requested forecast data.

        Returns
        -------
        data : DataFrame
            column names are the weather model's variable names.
        """
        self.latitude = location.latitude
        self.longitude = location.longitude
        self.altitude = location.altitude
        self.location = location
        
        url = self.address+'solar/'+str(self.longitude)+'/'+str(self.latitude)
        r = json.loads(requests.get(url, headers={'Authorization': 'Basic ' + self.apikey}).text)
        
        cols = list(dict(r['timesteps'][0]['models']['COSMO_DE']).keys())
        vals = [[y[w] for w in cols] for y in [x["models"]['COSMO_DE'] for x in r['timesteps']]]
        
        self.data = pd.DataFrame(vals, columns=cols)
        self.data['date'] = pd.to_datetime(self.data['date'])
        self.data = self.data.set_index('date')
        self.data = self.data.tz_localize(tz.utc).tz_convert(location.tz)
        
        return self.data

