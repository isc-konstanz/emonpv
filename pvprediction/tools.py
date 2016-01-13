#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pvprediction
    ~~~~~
    
"""
from datetime import timedelta
import os

import numpy as np
import pandas as pd


def get_parser():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    
    parser = ArgumentParser(description=__doc__)
    
    parser.add_argument('-f','--file', 
                        dest='forecastfile',
                        type=lambda x: _is_valid_file(parser, x),
                        help="Location of a solar irradiance forecast csv file to be processed", 
                        metavar='CSV')
    parser.add_argument('-d','--dir', 
                        dest='forecastdir',
                        help="Directory of solar irradiance forecast csv files, of which the newest one will be processed", 
                        metavar='DIR')
    parser.add_argument('-s','--simulation', 
                        dest='simulationdir',
                        help="Directory in which simulation output csv files will be placed", 
                        metavar='DIR')
    parser.add_argument('-o','--optimize', 
                        dest='optimize',
                        help='Disables efficiency optimization if "false"', 
                        metavar='DIR')
    return parser


def _is_valid_file(parser, arg):
    """
        Check if arg is a valid file that already exists on the file
        system.
        
    """
    arg = os.path.abspath(arg)
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg
