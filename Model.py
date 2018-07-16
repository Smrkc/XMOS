# -*- coding: utf-8 -*-
"""
Created on Wed Apr 04 13:13:48 2018

@author: evin
@brief: Class including the main data and their operations of the multimedia exposure meter app
        (Model of MVC)
"""
#import ThreadedSensor
#import bottle
#import Tobii
import config
from datetime import datetime
#import Scheduler
#from pydispatch import dispatcher
#from EventType import EventType
import Database
#from Questionnaire import Questionnaire
#from QuestionnaireType import QuestionnaireType
#from ActionType import ActionType
import rpiRecord
import Queue as queue
import os
import csv
from collections import defaultdict
import methodHelper
import threading
import gc

DIRPATH = os.getcwd()

class Model():
    """ Class including the main data and their operations of the multimedia exposure meter app
        (Model of MVC)
    """
    
    def __init__(self, masterFrame):
        """
        Initializes serverhost ip and port numbers & the sensors
        """
#        self.serverHostIP = config.getConfig().get("SERVER", "IP")
#        self.serverHostPort = config.getConfig().getint("SERVER", "Port")
        ################################################################################
        #initialize scheduler here by calling initScheduler method that will do the job
        ################################################################################
#        self.initScheduler()

        # hierarchy mapper
        self.helper = methodHelper.methodHelper()
        # load scenario
        self.reloadScenario()
        
        # initialize raspberry communication
        self.rpi = rpiRecord.RPI()
        
        #initialize sensors----------------------------------------------------
#        self.initTobiiEyeTracker()        
#        self.Quest = Questionnaire(masterFrame)

    # These three methods will probably go into separate module, depends on desired MVC structure
    def groupEvent(self, action):
        """group events in dictionary with common key index"""
        tempDict = defaultdict(list)
        for a in action:
            ex = a.pop("exec")
            tempDict[int(ex)].append(a)
        return tempDict

    def reloadScenario(self):
        """parse csv to get time events, action events and after action events"""
     
        self.timeEvent = []
        actionEvent = []
        onEvent = []
#        guiEvent = []
        self.positionDict = {}

        filename = config.CONFIG.get("SCENARIO", "filename")
        scenarioFilename = os.path.join(DIRPATH, "scenario", filename)
                
        with open(scenarioFilename, "rU") as inp:
            reader = csv.reader(inp, delimiter=";")
            headers = reader.next()
            for row in reader:
                if row[0] == "timeD":
                    self.timeEvent.append({headers[i]:row[i] for i in range(1, len(row)) if row[i]})
                elif row[0] == "onNextButton":
                    actionEvent.append({headers[i]:row[i] for i in range(1, len(row)) if row[i]})
#                elif row[0] == "updateGUI":
#                    guiEvent.append({headers[i]:row[i] for i in range(1, len(row)) if row[i]})
                elif row[0] == "waitOnQueue":
                    onEvent.append({headers[i]:row[i] for i in range(1, len(row)) if row[i]})
                else:
                    print "you have not selected appropriate event"
        # restructure so that actions that should execute together are on the same index
        self.actionEventDict = self.groupEvent(actionEvent)
        self.onEventDict = self.groupEvent(onEvent)
#        self.guiDict = self.groupEvent(guiEvent)
        
        # needed for gui label
        for k, v in self.actionEventDict.items():
            for action in v:
                if "factorsLab" in action.keys():
                    self.positionDict[k] = action["factorsLab"]
                    break

#        self.scenario =  [x[1].split(",") for x in list(self.configuration.items('LEGACY'))]               
        self.queue = queue.Queue()
        self.pos = 0                       

    def actionStarter(self, actions):
        """Method for starting actions in threads. It relies on methodHelper for code structure"""

        self.threads = []
        for t in actions:
            print "Action: {}".format(t)
            # func may be a class, a method or a function
            func = t.pop("function")
            t.update({"queue":self.queue})
            # check if it's a func without class
            func_module = self.helper.getFunctionModule(func)
            # check if it's a method within class
            func_c_module = self.helper.getFunctionClassModule(func)

            if func_module:
                # this function has no class, so we run directly
                mod = __import__(func_module)
                some_thread = threading.Thread(target=getattr(mod, func)(**t))
                self.threads.append(some_thread)
            elif func_c_module:
                # this is a method within a class
                # get class of function
                cls = self.helper.getFunctionClass(func)
                mod = __import__(func_c_module)
                # some classes are already instantiated, because we need sockets to stay alive
                for instance in gc.get_objects():
                    if isinstance(instance, getattr(mod, cls)):
                        # get first class instance (this won't work for multiple instances)
                        obj = instance    
                        # set required attributes from scenario
#                        for name, value in t.items():
#                            setattr(obj, name, value)
#                        # add queue
#                        setattr(obj, "queue", self.queue)
                        break
                else:
                    # if class is not yet instantiated, do it here
                    obj = getattr(mod, cls)()
                # run threaded method
                some_thread = threading.Thread(target=getattr(obj, func)(**t))
                self.threads.append(some_thread)
            else:
                # our function is actually a threading class
                module = self.helper.getClassModule(func)
                mod = __import__(module)
                self.threads.append(getattr(mod, func)(**t))
  
        for x in self.threads:
            x.start()
    
#    for x in self.model.guiDict[self.model.pos]:
#       getattr(locals()["self"], x["function"])()  
    
#    def initScheduler(self):
#        """
#        Create a Scheduler and ThreadedScheduler
#        (this will run the Sceheduler class in a thread like ThreadedSensor for tobii) 
#        class like in initTobiiEyeTracker method
#        """
#        self.scheduler = Scheduler.Scheduler()
#    
#    def initTobiiEyeTracker(self):
#        """
#        Initializes TOBII eyetracker sensor and starts the bottle application        
#        """
#        __tobiiConfigSection = "TOBII"
#        self.tobiiSensor = Tobii.Tobii(__tobiiConfigSection)
#        self.tobiiEyeTracker = ThreadedSensor.ThreadedSensor(self.tobiiSensor, __tobiiConfigSection)
#        
#        __tobiiEyeTrackerServerHostRoute = config.getConfig().get(__tobiiConfigSection, "HostRoute")
#        
#        print "Starting http server on http://",self.serverHostIP,':',self.serverHostPort, __tobiiEyeTrackerServerHostRoute
#        bottle.route(__tobiiEyeTrackerServerHostRoute)(self.tobiiEyeTracker.sensor.respondTracker)         
     
    def start(self, userName):
        """
        Session start time is set and the sensors are started for listening the ports
        """
        self.startTime = datetime.now()
        #create Database userPropsDict once
        Database.userPropsDict = Database.createUserPropsDict(userName, self.startTime)
        
        ################################################################################
        #Start the scheduler here
        ################################################################################
#        self.scheduler.setSessionStartTimeAndActionUnits(self.startTime)
#        self.scheduler.startScheduler()

        # execute all time events with timeout
        self.actionStarter(self.timeEvent)
       
        #start time should be set before starting listening the port
#        self.tobiiSensor.setSessionStartTime(startTime)
#        self.tobiiEyeTracker.startListening()

    def next_position(self):
        
#        self.scheduler.add_job(self.RPI.record())
        self.actionStarter(self.actionEventDict[self.pos])      
        
    def stop(self):
        """
        Sensors are stopped to listening the ports
        """
#        dispatcher.send(EventType.PlayAudioAndOpenQuestSignal, EventType.PlayAudioAndOpenQuestSender, ActionType.QuestionnaireActionUnit, "media/postQuestionnaire.ogg", "Post Questionnaire", QuestionnaireType.PostQuest, "questionnaire/post_questions.csv")
#            
#        dispatcher.send(EventType.PrintMessageSignal, EventType.PrintMessageSender, ActionType.EventAction, "The session is going to be stopped.")
        
#        self.tobiiEyeTracker.stopListening()
        try:
            # stop threads (not implemented for RPI class)            
            for t in self.threads:
                t.stop()
        except AttributeError:
            pass
    
       
        
#    def stopScheduler(self):
#        """
#        Stops scheduler, It should be called after messagebox is showed to user before are you sure to exit.
#        """
#        self.scheduler.stopScheduler()
        
#    def assignEventHandlers(self):
#        self.tobiiSensor.eyeGazeGreaterThanThreshold += self.scheduler.printText
#first benchmark commented out
#    progressBarMaxVal = 2
#    """Progress Bar's max value """
#    progressBarMinVal = 0
#    """Progress Bar's min value """
    
#    def start(self, slideVal):
#        result = 2* slideVal**2
#        print slideVal
#        print result
#        return result
         