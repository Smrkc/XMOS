# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 11:43:23 2018

@author: evin
@brief: Creates a configuration parser with provided inputs

"""
from ConfigParser import ConfigParser
import os

DEFAULT_CONFIG_FILE = 'config.ini'

def getConfigFile():
    return os.environ.get('CONFIG_FILE', DEFAULT_CONFIG_FILE)

CONFIG_FILE = getConfigFile()

def createConfig(configFile=None):
    parser = ConfigParser()
    parser.read(configFile or CONFIG_FILE)
    return parser

CONFIG = createConfig()

def getConfig():
    return CONFIG