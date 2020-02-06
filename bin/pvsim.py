#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    pvsyst
    ~~~~~~
    
    To learn how to configure the photovoltaic yield calculation, see "pvsyst --help"

"""
import logging.config

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))

import copy
import inspect
import pytz as tz
import pandas as pd
import datetime as dt
import concurrent.futures as futures

from argparse import ArgumentParser, RawTextHelpFormatter
from configparser import ConfigParser


def main(args):
    from core.system import Systems
    
    settings_file = os.path.join(args.config_dir, 'settings.cfg')
    if not os.path.isfile(settings_file):
        raise ValueError('Unable to open simulation settings: {}'.format(settings_file))
    
    settings = ConfigParser()
    settings.read(settings_file)
    
    systems = Systems()
    systems.read(**dict(settings.items('General')), **vars(args), package='pvsyst')
    
    start = tz.utc.localize(dt.datetime.strptime(settings['General']['start'], '%d.%m.%Y'))
    stop = tz.utc.localize(dt.datetime.strptime(settings['General']['stop'], '%d.%m.%Y'))
    for system in systems:
        system_dir = system._configs['General']['data_dir']
        database = copy.deepcopy(system._database)
        database.dir = os.path.join(system_dir, 'results')
        database.format = '%Y%m%d'
        database.disabled = False
        
        with futures.ThreadPoolExecutor() as executor:
            future = executor.submit(system._database.get, start, stop)
            
            results = system.run(**dict(settings.items('General')))
            results['p_ref'] = future.result()['pv_power']
            results['p_err'] = results['p_mp'] - results['p_ref']
            for _, result in results.groupby([results.index.date]):
                database.persist(result)
            
            # FIXME: Optional outlier cleaning
            #results = results[(results['p_err'] < results['p_err'].quantile(.95)) & (results['p_err'] > results['p_err'].quantile(.05))]
            hours = results.loc[:,'p_err'].groupby([results.index.hour])
            median = hours.median()
            median.name = 'median'
            desc = pd.concat([median, hours.describe()], axis=1).loc[:, ['count', 'median', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
            desc.to_csv(os.path.join(system_dir, 'results.csv'), sep=database.separator, decimal=database.decimal, encoding='utf-8')
            
            try:
                import seaborn as sns
                
                plot = sns.boxplot(x=results.index.hour, y='p_err', data=results, palette='Blues_d')
                plot.set(xlabel='hours', ylabel='Error [W]')
                plot.figure.savefig(os.path.join(system_dir, 'results.png'))
            
            except ImportError:
                pass


def _get_parser(root_dir, config_dir):
    from pvsyst import __version__
    
    parser = ArgumentParser(description=__doc__, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-v', '--version',
                         action='version',
                         version='%(prog)s {version}'.format(version=__version__))
    
    parser.add_argument('-r','--root-directory',
                        dest='root_dir',
                        help="directory where the package and related libraries are located",
                        default=root_dir,
                        metavar='DIR')
    
    parser.add_argument('-c','--config-directory',
                        dest='config_dir',
                        help="directory to expect configuration files",
                        default=config_dir,
                        metavar='DIR')
    
    return parser

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.abspath(inspect.getsourcefile(main)))
    if os.path.basename(root_dir) == 'bin':
        root_dir = os.path.dirname(root_dir)
    
    os.chdir(root_dir)
    
    config_dir = os.path.join(root_dir, 'conf')
    
    # Load the logging configuration
    loggingfile = os.path.join(config_dir, 'logging.cfg')
    logging.config.fileConfig(loggingfile)
    logger = logging.getLogger('pvsim')
    
    main(_get_parser(root_dir, config_dir).parse_args())

