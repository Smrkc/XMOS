# -*- coding: utf-8 -*-
"""
Created on Wed Apr 04 13:13:48 2018

@author: evin
@brief: Class establishing communication between user interface(view) and model.
       (Controller of MVC)
"""
import Model
import View
import Tkinter as Tk
#import tkMessageBox
#import bottle
#import EnableCors
#import threading
#import StoppableWSGIRefServer
#import config
#from pydispatch import dispatcher
#import SchedulerHelperMethods
#from EventType import EventType
#from ActionType import ActionType
import logging
import Queue as queue


class Controller():
    """Class establishing communication between user interface(view) and model.
       (Controller of MVC)
    """

    def __init__(self):
        """
        Initializes the bottle server, creates Model and View part of the MVC,
        and binds the start and stop button
        """
        self.logger = logging.getLogger(__name__)
#        self.initializeBottleServer()
        self.root = Tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.model = Model.Model(self.root)
        self.view = View.View(self.root)
           
#        self.view.sidePanel.startButton.bind("<Button>", self.start)
#        self.view.sidePanel.nextButton.bind("<Button>", self.nextPressed)
#        self.view.sidePanel.stopButton.bind("<Button>", self.stop)
        
        self.view.sidePanel.startButton.config(command=lambda : self.start(self.view.mainPanel.userNameVar))
        self.view.sidePanel.nextButton.config(command=self.nextPressed)
        self.view.sidePanel.stopButton.config(command=self.stop)
        
        self.view.mainPanel.userNameVar.trace("w", self.updateStartButtonState)
#        self.root.after(2000, self.root.focus_force)
        self.root.after(100, self.check_queue)
#        self.root.after(1000, self.updateTimer)
#        #connects OpenQuestSignal to openQuestionnaire method through dispatcher
#        dispatcher.connect(self.openQuestionnaire, signal=EventType.OpenQuestSignal, sender=EventType.OpenQuestSender)
#        #connects PlayAudioAndOpenQuestSignal to playAudioAndOpenQuestionnaire method through dispatcher
#        dispatcher.connect(self.playAudioAndOpenQuestionnaire, signal=EventType.PlayAudioAndOpenQuestSignal, sender=EventType.PlayAudioAndOpenQuestSender)       
#        #since the questionnaire can not be opened form dispatcher(another thread) '<<pingOpenQuestionnaire>>' is binded to self.pingOpenQuestionnaire method
#        self.root.bind('<<pingOpenQuestionnaire>>', self.pingOpenQuestionnaire)
#        #since the questionnaire can not be opened form dispatcher(another thread) '<<pingPlayAudioAndOpenQuestionnaire>>' is binded to self.pingPlayAudioAndOpenQuestionnaire method
#        self.root.bind('<<pingPlayAudioAndOpenQuestionnaire>>', self.pingPlayAudioAndOpenQuestionnaire)
        
        
    def run(self):
        """
        starts the user interface
        """
        self.root.title("MVC")
        self.root.deiconify()
        self.root.mainloop()
        
    def start(self, user):
        """
        Orginizes the start&stop buttons state and signals the model to start listening the sensors
        """
        self.logger.info("BUTTON START")
        #since bind does not work like command you have to check the state
        if self.view.sidePanel.startButton["state"] == "normal":
            self.view.sidePanel.startButton.config(state="disabled")
            self.view.sidePanel.stopButton.config(state="normal")
#            self.view.sidePanel.nextButton.config(state="normal")
            self.model.start(user.get())
            if self.model.pos in self.model.actionEventDict.keys():
                self.view.mainPanel.positionLabel1.config(text="current: {}".format(self.model.positionDict[self.model.pos]))
        
        
    def stop(self):
        """
        Changes the start&stop buttons state and signals the model to stop listening the sensors
        """
        
        self.logger.info("BUTTON STOP")
        #since bind does not work like command you have to check the state
        if self.view.sidePanel.stopButton["state"] == "normal":
#            if self.view.mainPanel.userNameVar.get().strip():
            self.view.sidePanel.startButton.config(state="normal")                
            self.view.sidePanel.stopButton.config(state="disabled")
            self.view.sidePanel.nextButton.config(state="disabled")
        self.model.stop()
        # reload scenario
        self.model.reloadScenario()
        
        
    def nextPressed(self):
               
        self.logger.info("BUTTON NEXT")
        self.model.pos += 1
        self.view.sidePanel.nextButton.config(state="disabled")
        # this is just for displaying current and next position of recording device
        if self.model.pos in self.model.actionEventDict.keys():
            self.view.mainPanel.positionLabel1.config(text="current: {}".format(self.model.positionDict[self.model.pos]))
#            self.view.mainPanel.positionLabel2.config(text="next: {}".format(self.model.positionDict[self.model.pos + 1]))
        self.model.next_position()


    def nextButton(self, **kwargs):
        if self.view.sidePanel.stopButton["state"] == "normal":
            self.view.sidePanel.nextButton.config(state="normal")
    
    def check_queue(self):
        # the only way to get real time response from working threads - tkinter limitation
        # reference: http://stupidpythonideas.blogspot.com/2013/10/why-your-gui-app-freezes.html
        while True:
            try:
                # try to get queue object
                task = self.model.queue.get_nowait()#(block=False, 100)
            except queue.Empty:
                # break out of loop if there's no queue
                break
            else:
                print task
                self.logger.info("Event completed at {}".format(task))
                # onEvent actions are executed here because this way we avoid 
                # implementation of handling events for task complete
                if self.model.pos in self.model.onEventDict.keys():
                    self.model.actionStarter(self.model.onEventDict[self.model.pos])
                # gui actions are executed here because only controller has acess to view 
                # if methods will have arguments, you need to implement it
                
                # gui se je spremenil v waitOnQueue, kar pomeni da bo shranjen
                # v isti dict kot onEventDict, zato preveri, če je delovanje od
                # actionStarter kompatibilno
#                for x in self.model.guiDict[self.model.pos]:
#                    getattr(locals()["self"], x["function"])()    
                try:
                    # let root know that the task is completed
                    self.root.after_idle(task)
                except AttributeError:
                    break
                    
        self.root.after(100, self.check_queue)
    
    
#    def updateTimer(self):
#        
#        time = datetime.now() - self.model.startTime 
#        self.view.mainPanel.trackTimer.config(text=time.seconds)
#        self.root.after(1000, self.updateTimer)
    
    
    def onClosing(self):
        """
        A message box is showed to the user before closing the window and model is signaled
        to stop listening the sensors and bottle server is stooped and window is destroyed
        """
        # destroy GUI
        self.root.destroy()
        # stop all threads
        self.model.stop()
        # close socket
        self.model.rpi.close_socket()        
#        if tkMessageBox.askokcancel("Quit", "Do you want to quit?"):
            #if the button stop is already pushed don't call stop method again
#        state = str(self.view.sidePanel.stopButton["state"])
#        if state == "normal":
#            self.model.stop()
##        self.server.stop()
#        self.root.destroy()
#        self.model.stopScheduler()
            
#    def initializeBottleServer(self):
#        """
#        Starts the bottle server
#        """
#        app = bottle.app()
#        app.install(EnableCors.EnableCors())
#        
#        __serverHostIP = config.getConfig().get("SERVER", "IP")
#        __serverHostPort = config.getConfig().getint("SERVER", "Port")
#        print "Starting http server on http://",__serverHostIP,':',__serverHostPort
#        
#        self.server = StoppableWSGIRefServer.StoppableWSGIRefServer(host=__serverHostIP, port=__serverHostPort)
#    
#        self.appThread = threading.Thread(target=app.run, kwargs=dict(server=self.server))
#        self.appThread.daemon = True
#        self.appThread.start()
    
    def updateStartButtonState(self, *_):
        """
        The start button is enabled if only username is provided
        """
        if (self.view.sidePanel.stopButton["state"] =="disabled" and self.view.mainPanel.userNameVar.get()):
            self.view.sidePanel.startButton.config(state="normal")
        else:
            self.view.sidePanel.startButton.config(state="disabled")
        self.view.mainPanel.userNameEntry.focus_set()

    
#    def openQuestionnaire(self, questTitle, questType, questFileName):
#        """
#        Receives openquestionnaire event and generates ping event for tkinter to be able to pop up questionnaire window
#        """
#        self.questTitle = questTitle
#        self.questType = questType
#        self.questFileName = questFileName
#        self.root.event_generate('<<pingOpenQuestionnaire>>', when='tail')
#        
#    def pingOpenQuestionnaire(self, event):
#        """
#        After OpenQuestSignal received and ping event generated, event is catched here and opened as a pop up window
#        """
#        SchedulerHelperMethods.openQuestionnaire(ActionType.QuestionnaireActionUnit, self.root, self.questTitle, self.questType, self.questFileName)
#        
#    def playAudioAndOpenQuestionnaire(self, actionType, audioFileName, questTitlePAO, questTypePAO, questFileNamePAO):
#        """
#        Receives playAudioAndopenquestionnaire event and generates ping event for playing sound and tkinter to be able to  pop up questionnaire window
#        """
#        self.questTitlePAO = questTitlePAO
#        self.questTypePAO = questTypePAO
#        self.questFileNamePAO = questFileNamePAO
#        self.audioFileName = audioFileName
#        self.actionTypePAO = actionType
#        self.root.event_generate('<<pingPlayAudioAndOpenQuestionnaire>>', when='tail')
#        
#    def pingPlayAudioAndOpenQuestionnaire(self, event):
#        """
#        After PlaySoundAndOpenQuestSignal received and ping event generated, event is catched here SchedulerHelperMethods method is called
#        """
#        SchedulerHelperMethods.playSoundAndOpenQuestionnaire(self.actionTypePAO, self.audioFileName, self.questTitlePAO, self.questTypePAO, self.questFileNamePAO)
#        
  