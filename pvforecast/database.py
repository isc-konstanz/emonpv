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


    def post(self, system, data, **kwargs):
        for database in reversed(self.values()):
            database.post(system, data, **kwargs)


    def get(self, system, start, end, interval, **kwargs):
        database = next(iter(self.values()))
        database.get(system, start, end, interval, **kwargs)


class Database(ABC):

    def __init__(self, timezone='UTC'):
        self.timezone = tz.timezone(timezone)


    @abstractmethod
    def get(self, system, start, end, interval, **kwargs):
        """ 
        Retrieve data for a specified time interval of a set of data feeds
        
        :param system: 
            the system for which the values will be looked up for.
        :type keys: 
            :class:`pvforecast.system.System`
        
        :param start: 
            the start time for which the values will be looked up for.
            For many applications, passing datetime.datetime.now() will suffice.
        :type start: 
            :class:`pandas.tslib.Timestamp` or datetime
        
        :param end: 
            the end time for which the data will be looked up for.
        :type end: 
            :class:`pandas.tslib.Timestamp` or datetime
        
        :param interval: 
            the time interval in seconds, retrieved values shout be returned in.
        :type interval: 
            int
        
        
        :returns: 
            the retrieved values, indexed in a specific time interval.
        :rtype: 
            :class:`pandas.DataFrame`
        """
        pass


    @abstractmethod
    def last(self, system, interval, **kwargs):
        """
        Retrieve the last recorded values for a specified set of data feeds
        
        :param system: 
            the system for which the values will be looked up for.
        :type keys: 
            :class:`pvforecast.system.System`
        
        :param interval: 
            the time interval in seconds, retrieved values shout be returned in.
        :type interval: 
            int
        """
        pass


    @abstractmethod
    def post(self, system, data, **kwargs):
        """ 
        Post a set of data values, to persistently store them on the server
        
        :param system: 
            the system for which the values will be looked up for.
        :type keys: 
            :class:`pvforecast.system.System`
        
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


    def get(self, keys, start, end, interval, _):
        data = pd.DataFrame()
        for key in keys:
            result = self.feeds[key].data(start, end, interval, self.timezone)
            result.name = key
            
            data = pd.concat([data, result], axis=1)
        
        return data


    def last(self, keys, _):
        feeds = OrderedDict()
        for key in keys:
            feeds[key] = self.feeds[key]
        
        return self.connection.fetch(feeds)


    def post(self, system, data, _):
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


    def get(self, keys, start, end, interval, _):
        if interval > 900:
            offset = (start - start.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() % interval
            data = self.data[keys].resample(str(int(interval))+'s', base=offset).sum()
        else:
            data = self.data[keys]
        
        if start < end:
            return data.loc[start:end+dt.timedelta(seconds=interval)]
        else:
            return data.truncate(before=start).head(1)


    def last(self, keys, interval, _):
        date = dt.datetime.now(tz.utc).replace(second=0, microsecond=0)
        if date.minute % (interval/60) != 0:
            date = date - dt.timedelta(minutes=date.minute % (interval/60))
        
        return self.get(keys, date, date, interval)


    def post(self, system, data, datatype='yield'):
        if data is not None:
            latitude = system.location.latitude
            longitude = system.location.longitude
            
            if datatype == 'weather':
                latitude = round(latitude, 3)
                longitude = round(longitude, 3)
            
            path = os.path.join(self.datadir, datatype, str(latitude) + '_' + str(longitude))
            if not os.path.exists(path):
                os.makedirs(path)
            
            self.write_file(path, data)


    def read_file(self, path, index_column='unixtimestamp', unix=True):
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
                
            csv.index = csv.index.tz_localize(tz.timezone('UTC')).tz_convert(self.timezone)
        
        csv.index.name = 'time'
        
        return csv


    def read_nearest_file(self, date, path, index_column='time'):
        """
        Reads the daily content from a CSV file, closest to the passed date, 
        following the file naming scheme "YYYYMMDD*.filename"
        
        
        :param date: 
            the date for which a filename file will be looked up for.
        :type date: 
            :class:`pandas.tslib.Timestamp` or datetime
        
        :param path: 
            the directory, containing the filename files that should be looked for.
        :type path:
            str or unicode
        
        :param index_column: 
            the name of the column, that will be used as index. The index will be assumed 
            to be a time format, that will be parsed and localized.
        :type index_column:
            str or unicode
        
        :param timezone: 
            the timezone, in which the data is logged and available in the filename file.
            See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
            valid time zones.
        :type timezone:
            str or unicode
        
        
        :returns: 
            the retrieved columns, indexed by their date
        :rtype: 
            :class:`pandas.DataFrame`
        """
        csv = None
        
        ref = int(date.strftime('%Y%m%d'))
        diff = 1970010100
        filename = None
        try:
            for f in os.listdir(path):
                if f.endswith('.csv'):
                    d = abs(ref - int(f[0:8]))
                    if (d < diff):
                        diff = d
                        filename = f
        except IOError:
            logger.error('Unable to find data files in "%s"', path)
        else:
            if(filename == None):
                logger.error('Unable to find data files in "%s"', path)
            else:
                csvpath = os.path.join(path, filename)
                csv = self.read_file(csvpath, index_column=index_column, unix=False)
        
        return csv


    def write_file(self, path, data):
        filename = data.index[0].astimezone(self.timezone).strftime('%Y%m%d_%H%M%S') + '.csv';
        filepath = os.path.join(path, filename)
        
        data.index.name = 'time'
        data.tz_convert(self.timezone).astype(float).round(3).to_csv(filepath, sep=self.separator, decimal=self.decimal, encoding='utf-8')


    def concat_file(self, path, data):
        filename = data.index[0].astimezone(self.timezone).strftime('%Y') + '_opt.csv';
        filepath = os.path.join(path, filename)
        
        data.index.name = 'time'
        
        if os.path.isfile(filepath):
            csv = pd.read_csv(filepath, sep=self.separator, decimal=self.decimal, index_col='time', parse_dates=['time'])
            csv.index = csv.index.tz_localize(tz.utc).tz_convert(self.timezone)
        else:
            csv = pd.DataFrame()
        
        # Concatenate data to existing file
        # Preserve column order, as pandas concatenation may sort them as result of a bug (https://github.com/pandas-dev/pandas/issues/4588)
        csv = pd.concat([csv, data.tz_convert(self.timezone)])
        csv[data.columns].astype(float).round(3).to_csv(filepath, sep=self.separator, decimal=self.decimal, encoding='utf-8')

