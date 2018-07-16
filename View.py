# -*- coding: utf-8 -*-
"""
Created on Wed Apr 04 13:12:21 2018

@author: evin
@brief: The user interface(GUI) of multimedia exposure meter app.
        (View of MVC)
"""

import Tkinter as Tk

class View():
    """ The user interface(GUI) of multimedia exposure meter app.
        (View of MVC)
    """
    
    def __init__(self, master):
        self.frame = Tk.Frame(master)
        self.frame.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        self.mainPanel = MainPanel(master)
        self.sidePanel = SidePanel(master)

class MainPanel():
    """Class including visuals: entrys, labels, graphs, sliders etc.
    
    """
    def __init__(self, root):
        self.initUserNameFrame(root) 
        
    def initUserNameFrame(self, root):
        self.userNameVar = Tk.StringVar()
        self.frame4 = Tk.Frame(root)
        self.frame4.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        self.userNameLabel = Tk.Label(self.frame4, text="User Name:")
#        self.userNameLabel.grid(row=2, column=1, sticky="w")
        self.userNameLabel.pack(side=Tk.LEFT)
        self.userNameEntry = Tk.Entry(self.frame4, width=11, textvariable=self.userNameVar)
#        self.userNameEntry.grid(row=2, column=2, sticky="e")
        self.userNameEntry.pack(side=Tk.RIGHT)
        self.userNameEntry.focus()
        self.positionLabel2 = Tk.Label(self.frame4, text="")
        self.positionLabel2.pack(side=Tk.BOTTOM)
        self.positionLabel1 = Tk.Label(self.frame4, text="")
        self.positionLabel1.pack(side=Tk.BOTTOM)
        
   
        
class SidePanel():
    """Class managing the start and stop buttons.
    
    """
    def __init__(self, root):
        self.frame3 = Tk.Frame(root)
        self.frame3.pack(side=Tk.RIGHT, fill=Tk.BOTH, expand=1)
        self.startButton = Tk.Button(self.frame3, text="Start", state="disabled")
        self.startButton.pack(side="top",fill=Tk.BOTH)
        self.nextButton = Tk.Button(self.frame3, text="Next", state="disabled")
        self.nextButton.pack(side="top",fill=Tk.BOTH)
        self.stopButton = Tk.Button(self.frame3, text="Stop", state="disabled")
        self.stopButton.pack(side="top",fill=Tk.BOTH)
