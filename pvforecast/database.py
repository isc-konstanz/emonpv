# -*- coding: utf-8 -*-
"""
    theoptimization.database
    ~~~~~
    
    
"""
import logging
logger = logging.getLogger(__name__)

import os
from abc import ABC, abstractmethod
import datetime as dt
import pytz as tz
import pandas as pd
import numpy as np

from collections import OrderedDict
from configparser import ConfigParser
from emonpy import Emoncms, EmoncmsData


class DatabaseList(OrderedDict):

    def __init__(self, configs, **kwargs):
        super(DatabaseList, self).__init__(**kwargs)
        
        # Read the systems database settings
        settingsfile = os.path.join(configs.get('General', 'configdir'), 'database.cfg')
        settings = ConfigParser()
        settings.read(settingsfile)
        
        timezone = settings.get('General', 'timezone')
        
        for database in settings.get('General', 'enabled').split(','):
            key = database.lower()
            if key == 'emoncms':
                self[key] = EmoncmsDatabase(configs, timezone=timezone)
                
            elif key == 'csv':
                self[key] = CsvDatabase(configs, timezone=timezone)


    def post(self, system, location, data, **kwargs):
        for database in reversed(self.values()):
            database.post(system, location, data, datatype='system', **kwargs)


    def get(self, system, location, start, end, interval, **kwargs):
        database = next(iter(self.values()))
        database.get(system, location, start, end=end, interval=interval, datatype='system', **kwargs)


class Database(ABC):

    def __init__(self, timezone='UTC'):
        self.timezone = tz.timezone(timezone)


    @abstractmethod
    def get(self, system, location, time, **kwargs):
        """ 
        Retrieve data for a specified time interval of a set of data feeds
        
        :param system: 
            the system for which the values will be looked up for.
        :type keys: 
            :class:`pvforecast.system.System`
        
        :param location: 
            the location for which the values will be looked up for.
        :type keys: 
            :class:`pvlib.location.Location`
        
        :param time: 
            the time for which the values will be looked up for.
            For many applications, passing datetime.datetime.now() will suffice.
        :type time: 
            :class:`pandas.tslib.Timestamp` or datetime
        
        :returns: 
            the retrieved values, indexed in a specific time interval.
        :rtype: 
            :class:`pandas.DataFrame`
        """
        pass


    @abstractmethod
    def post(self, system, location, data, **kwargs):
        """ 
        Post a set of data values, to persistently store them on the server
        
        :param system: 
            the system for which the values will be looked up for.
        :type keys: 
            :class:`pvforecast.system.System`
        
        :param location: 
            the location for which the values will be looked up for.
        :type keys: 
            :class:`pvlib.location.Location`
        
        :param data: 
            the data set to be posted
        :type data: 
            :class:`pandas.DataFrame`
        """
        pass


class EmoncmsDatabase(Database):

    def __init__(self, configs, timezone='UTC'):
        super().__init__(timezone=timezone)
        
        settingsfile = os.path.join(configs.get('General', 'configdir'), 'database.cfg')
        settings = ConfigParser()
        settings.read(settingsfile)
        
        emoncmsfile = settings.get('Emoncms', 'configs')
        emoncms = ConfigParser()
        emoncms.read(emoncmsfile)
        
        self.node = settings.get('Emoncms','node')
        self.connection = Emoncms(emoncms.get('Emoncms','address'), emoncms.get('Emoncms','authentication'))


    def get(self, system, location, start, end, interval, **kwargs):
        pass


    def post(self, system, location, data):
        if 'apikey' in system:
            bulk = EmoncmsData(timezone=self.timezone)
            for time, row in data.iterrows():
                for key in data.columns:
                    value = row[key]
                    if value is not None and not np.isnan(value):
                        bulk.add(time, self.node, key.lower(), float(value))
            
            self.connection.post(bulk, apikey=system.apikey)


class CsvDatabase(Database):

    def __init__(self, configs, timezone='UTC'):
        super().__init__(timezone=timezone)
        
        settingsfile = os.path.join(configs.get('General', 'configdir'), 'database.cfg')
        settings = ConfigParser()
        settings.read(settingsfile)
        
        self.datadir = configs.get('General', 'datadir')
        self.decimal = settings.get('CSV', 'decimal')
        self.separator = settings.get('CSV', 'separator')


    def exists(self, system, location, time, datatype='weather'):
        return os.path.exists(self._build_file(system, location, time, datatype))


    def get(self, system, location, start, end=None, interval=None, datatype='weather'):
        data = self._read_file(self._build_file(system, location, start, datatype))
        
        if interval is not None and interval > 900:
            offset = (start - start.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() % interval
            data = data.resample(str(int(interval))+'s', base=offset).sum()
        
        if end is not None:
            if start > end:
                return data.truncate(before=start).head(1)
            
            return data.loc[start:end+dt.timedelta(seconds=interval)]
        
        return data


    def post(self, system, location, data, datatype='weather', **kwargs):
        if data is not None:
            path = self._get_dir(system, location, datatype)
            if not os.path.exists(path):
                os.makedirs(path)
            
            self._write_file(data, path, **kwargs)


    def _write_file(self, data, path, time):
        file = os.path.join(path, self._build_file_name(time))
        
        data.index.name = 'time'
        data.tz_convert(tz.utc).astype(float).to_csv(file, sep=self.separator, decimal=self.decimal, encoding='utf-8')


    def _read_file(self, path, index_column='time', unix=True):
        """
        Reads the content of a specified CSV file.
        
        :param path: 
            the full path to the CSV file.
        :type path:
            str or unicode
        
        :param index_column: 
            the name of the column, that will be used as index. The index will be assumed 
            to be a time format, that will be parsed and localized.
        :type index_column:
            str or unicode
        
        :param unix: 
            the flag, if the index column contains UNIX timestamps that need to be parsed accordingly.
        :type unix:
            boolean
        
        :param timezone: 
            the timezone, in which the data is logged and available in the data file.
            See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
            valid time zones.
        :type timezone:
            str or unicode
        
        
        :returns: 
            the retrieved columns, indexed by their date
        :rtype: 
            :class:`pandas.DataFrame`
        """
        csv = pd.read_csv(path, sep=',', decimal='.', 
                          index_col=index_column, parse_dates=[index_column])
        
        if not csv.empty:
            if unix:
                csv.index = pd.to_datetime(csv.index, unit='ms')
                
            csv.index = csv.index.tz_localize(tz.utc)
        
        csv.index.name = 'time'
        
        return csv


    def _build_file(self, system, location, time, datatype):
        return os.path.join(self._build_dir(system, location, datatype), self._build_file_name(time))


    def _build_file_name(self, time):
        return time.astimezone(tz.utc).strftime('%Y%m%d_%H%M%S') + '.csv';


    def _build_dir(self, system, location, datatype):
        if datatype == 'weather':
            location_key = str(location.latitude) + '_' + str(location.longitude)
        else:
            location_key = system.location_key
        
        return os.path.join(self.datadir, datatype, location_key)

