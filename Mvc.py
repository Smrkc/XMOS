# -*- coding: utf-8 -*-
"""
Created on Wed Apr 04 12:31:46 2018

@author: evin
@brief: Starting point of the multimedia exposure meter app
"""
import Controller
import logging
import os
from datetime import datetime
import platform
from config import CONFIG

DIRPATH = os.getcwd()

if __name__ == "__main__":
    """
    main (Starting point) of the multimedia exposure meter app
    """
    
    # log configuration
    loggerLocation = os.path.join(DIRPATH, "logs")
    
    if not os.path.exists(loggerLocation):
        os.makedirs(loggerLocation)
    
    currentDate = datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
    loggerFilename = os.path.join(loggerLocation, "RunExperiment_{}.log".format(currentDate))
    
      
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)-25s %(name)-18s %(threadName)-13s %(levelname)-16s %(message)s',
                        #datefmt="%Y-%m-%d %H-%M-%S",
                        filename=loggerFilename,
                        filemode="w")
    logger = logging.getLogger(__name__)   
    
    # put in platform and config data
    logger.info("Platform: {} {}".format(platform.platform(), platform.machine()))
    logger.info("Python: {}".format(platform.python_version()))
    logger.info("RunExperiment parameters:")
    for sect in CONFIG.sections():
        logger.info("{}: {}".format(sect.upper(), dict(CONFIG.items(sect))))
    logger.info("#"*50)
    logger.info("App initiated")    
    
    c = Controller.Controller()
    c.run()