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

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pvlib.forecast import ForecastModel


class Weather():
    
    def __init__(self, configs, database, model='COSMO_DE'):
        self.model = model
        if model == 'COSMO_DE':
            self.server = COSMO_DE(configs.get('W3Data', 'address'), 
                                   configs.get('W3Data', 'api_key'))
        else:
            raise ValueError('Invalid forecast model argument')
        
        if 'csv' in database:
            self.database = database['csv']
        else:
            self.database = None


    def forecast(self, system, time):
        forecast = self.server.get_processed_data(system.location)
        
        self.database.post(system, forecast, datatype='weather')
        return forecast


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
        self.api_key = api_key
        
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
        
        url = self.address+str(self.longitude)+'/'+str(self.latitude)
        r = json.loads(requests.get(url, headers={'Authorization': 'Basic ' + self.api_key}).text)
        
        cols = list(dict(r['timesteps'][0]['models']['COSMO_DE']).keys())
        vals = [[y[w] for w in cols] for y in [x["models"]['COSMO_DE'] for x in r['timesteps']]]
        
        self.data = pd.DataFrame(vals, columns=cols)
        self.data['date'] = pd.to_datetime(self.data['date'])
        self.data = self.data.set_index('date')
        self.data = self.data.tz_localize(tz.utc).tz_convert(location.tz)
        
        return self.data

