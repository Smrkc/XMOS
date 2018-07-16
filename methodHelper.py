# -*- coding: utf-8 -*-
"""
Created on Sat Jun 23 01:38:38 2018

@author: nejck

This is a "module -> class -> method" hierarchy implemented with namedtuples. 
It searches current directory for py files and extracts the hierarchy.

Example use:
    helper = methodHelper()
    print helper.getClassModule("WaveRecord")
    
result:
    >> rpiRecord

    helper = methodHelper()
    print helper.getClassFunction("WaveRecord")

result:
    >> ['run', '__init__']

reference:
    http://code.activestate.com/recipes/553262-list-classes-methods-and-functions-in-a-module/
"""



import inspect
import os
from collections import namedtuple

class methodHelper:
    
    def __init__(self):
        self.listTuples = []
        self.traverseDir()
        
        
    def traverseDir(self):
        """traverse only current folder -> subfolders not implemented, but look 
        at os.walk()"""
        
        for f in os.listdir(os.getcwd()):
            if f.endswith(".py"):
                module = f[:-3]
                try:
                    mod = __import__(module)
                    self.methodMap(mod)
                except BaseException:
                    continue
    
    def methodMap(self, mod):
        """create list of named tuples"""
        
        ANamedTuple = namedtuple("Hierarchy", "mdl cls fnc")
    
        for name in dir(mod):
            obj = getattr(mod, name)
    
            if inspect.isclass(obj):
                for name in obj.__dict__:
                    item = getattr(obj, name)
    
                    if inspect.ismethod(item):
                        self.listTuples.append(ANamedTuple(mdl=mod.__name__, cls=obj.__name__, fnc=item.__name__))
    
            elif (inspect.ismethod(obj) or inspect.isfunction(obj)):
                self.listTuples.append(ANamedTuple(mdl=mod.__name__, cls=None, fnc=obj.__name__))


    def getClassModule(self, cls):
        func = {x.mdl for x in self.listTuples if x.cls == cls}
        if func: 
            return func.pop()
        return None
 
    def getFunctionClassModule(self, function):
        """specifically meant for functions with classes"""
        func = {x.mdl for x in self.listTuples if (x.fnc == function) and x.cls}
        if func:
            return func.pop()
        return None    
    
    def getClassFunctions(self, cls):
        """get all functions of a class"""
        return list({x.fnc for x in self.listTuples if x.cls == cls})
    
    def getFunctionModule(self, function):
        """specifically meant for functions without classes"""
        func = {x.mdl for x in self.listTuples if (x.fnc == function) and not x.cls}
        if func:
            return func.pop()
        return None

    def getFunctionClass(self, function):
        """get specific function's class"""
        func = {x.cls for x in self.listTuples if (x.fnc == function)}
        if func:
            return func.pop()
        return None
        