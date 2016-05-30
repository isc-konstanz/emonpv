# -*- coding: utf-8 -*-
"""
    pvprediction.system
    ~~~~~
    
    This module provides functions to read defined :class:`pvprediction.System` 
    objects from a configuration file. Systems contain information about location,
    orientation and datasheet parameters of a specific photovoltaic installation.
    
"""
import logging
logger = logging.getLogger('pvprediction.systems')

import os
import json
import pvlib as pv

from configparser import ConfigParser


def read(configdir):
    """ 
    Reads a list of :class:`pvprediction.System`, defined in a specified
    configuration file. A System defines photovoltaic installations location,
    orientation and several datasheet parameters, necessary to calculate its
    generated power.

    :param configdir: 
        the directory containing the config files, specifying the System objects.
    
    :returns: 
        the dictionary of photovoltaic systems, specified in the configuration
        file. Listed System objects are indexed by their 
        specified section id.
    :rtype: 
        dict of :class:`pvprediction.System`
        
    """
    systems = {}
    
    # Read in the general settings, containing geographical and timezone parameters
    settingsfile = os.path.join(configdir, 'settings.cfg')
    settings = ConfigParser()
    settings.read(settingsfile)
    
    # Read in the default system properties, such as initial efficiency, covariance 
    # and the Standard Test Condition reference irradiation and temperature
    defaultfile = os.path.join(configdir, 'system_default.cfg')
    defaults = ConfigParser()
    defaults.read(defaultfile)
    
    # The data directory, a specific variable file will be created in for each system
    datadir = str(settings.get('General','datadir'))
    
    # Read the system orientation and datasheet parameters
    configfile = os.path.join(configdir, 'systems.cfg')
    config = ConfigParser()
    config.read(configfile)
    
    loc = pv.location.Location(float(settings.get('Location','latitude')), 
                               float(settings.get('Location','longitude')), 
                               altitude=float(settings.get('Location','altitude')),
                               tz=str(settings.get('Location','timezone')))
    
    for section in config.sections():
        logger.debug('System "%s" found', section)
        
        system = System(datadir, defaults.items('Default'), loc, 
                        section, config.items(section))
        
        systems[section] = system
    
    if not systems:
        logger.warn('System list is empty')
    
    return systems


class System:
    """
    The System object provides all necessary parameters, to define a 
    photovoltaic installation. It contains location, orientation and several 
    datasheet parameters, needed to be passed, to calculate a systems' 
    generated power.
    
    Provided functions handle the serialization of system specific variable 
    parameters, such as hourly efficiency values and optimization covariance,
    which get stored as a json dump in a defined directory.
    
    
    :param datadir:
        the directory in which variable parameters will be stored and retrieved.
    :type datadir:
        str or unicode
    
    :param defaults: 
        the default values, used for each specified system, such as initial 
        efficiency, covariance and the Standard Test Condition reference 
        irradiation and temperature
    :type defaults: 
        dict of str: str
    
    :param sysid: 
        the systems' identification
    :type sysid:
        str or unicode
    
    :param parameters: 
        the systems' orientation and datasheet parameters
    :type parameters: 
        dict of str: str
    
    :param location: 
        the systems' geographical specification, containing latitude, longitude, 
        altitude and timezone information.
    :type location: 
        :class:`pvlib.location.Location`
    """
    
    def __init__(self, datadir, defaults, location, sysid, parameters):
        self._datadir = datadir
        
        self.id = sysid
        self.location = location
        
        self.modules_param = {}
        for (key, value) in parameters:
            self.modules_param[key] = self._parse_parameter(value)
        
        self.system_param = self._load_parameters(defaults)
      
    
    def save_parameters(self):
        """
        Saves the systems' variable parameters, such as hourly efficiency values 
        and optimization covariance, from the instances' attributes. The data gets 
        stored as a json dump in the instances' defined data directory, named
        after the systems identification string.
        """
        paramfile = os.path.join(self._datadir, self.id.lower() + '.cfg')
        
        params_var = {}
        params_var['eta'] = self.system_param['eta']
        params_var['cov'] = self.system_param['cov']
        
        with open(paramfile, 'w') as paramjson:
            json.dump(params_var, paramjson)
    
    
    def _load_parameters(self, default):
        """
        Loads the systems' variable parameters, such as hourly efficiency values 
        and optimization covariance to the instances' attributes. If no parameters 
        were stored yet, a new file will be created, using the passed default values
        
        :param defaults: 
            the default values, used for each specified system, such as initial 
            efficiency, covariance and the Standard Test Condition reference 
            irradiation and temperature
        :type defaults: 
            dict of str: str
        """
        params = {}
        for (key, value) in default:
            params[key] = self._parse_parameter(value)
        
        if not os.path.exists(self._datadir):
            os.makedirs(self._datadir)
        
        # Check if the file already exists, and create a new one, using the 
        # passed default values, if necessary
        paramfile = os.path.join(self._datadir, self.id.lower() + '.cfg')
        if (os.path.isfile(paramfile)):
            paramjson = open(paramfile)
            params_var = json.load(paramjson)
            params.update(params_var)
        else:
            params_var = {}
            params_var['eta'] = [params['eta']]*24
            params_var['cov'] = [params['sigma']**2]*24
            params.update(params_var)
            
            with open(paramfile, 'w') as paramjson:
                json.dump(params_var, paramjson)
            
        return params
    
    
    def _parse_parameter(self, parameter):
        try:
            return int(parameter)
        except ValueError:
            return float(parameter)
        