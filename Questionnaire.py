# -*- coding: utf-8 -*-
"""
Created on Fri May 25 11:21:49 2018

@author: Nejc Kozjek

"""

"""
@arrangementAuthor: EvinA
The class for opening a questionnaire pop up window with given inputs
Please note that there are two sections in [QUESTIONNAIRE] header. DBCollectionName and FinalAnswersCollectionName
In DBCollectionName every move of the user is saved to DB, like forwarding coming back etc.
In FinalAnswersCollectionName the final answers to the questions are stored for easy using later for analysis
"""
from Tkinter import *
import ttk
from datetime import datetime
from csvReader import csvReader
from collections import OrderedDict
import Database
from itertools import groupby,izip
import os
import logging

DIRPATH = os.getcwd()
QUESTIONNAIREPATH = os.path.join(DIRPATH, "questionnaire")

if not os.path.exists(QUESTIONNAIREPATH):
    os.makedirs(QUESTIONNAIREPATH)

class Questionnaire():
    def __init__(self, masterFrame, title=None, questType=None, filename=None, queue=None, nextActTrig=None):
        
        self.logger = logging.getLogger(__name__)
        self.dbSectionName ="QUESTIONNAIRE"
        self.finalAnswersCollectionName = "FinalAnswersCollectionName"
        # load questions
        self.filename = filename
        self.questType = questType
        self.masterFrame = masterFrame
        self.title = title
        self.queue = queue
        self.nextActTrig = nextActTrig
        #nb.run()
    
    def openQuestionnaire(self):
        
        self.logger.debug("Open questionnaire {}".format(self.filename))
        self.questionFilePath = os.path.join(QUESTIONNAIREPATH, self.filename)
        csr = csvReader(self.questionFilePath, ";")
        csr.make_questions()
        self.questions = csr.questionnaire
        self.questionnaireConf = csr.getQuestionnaireConf()        
        self.initGUI()
        # create notebook
        self.add_start()
        for i in range(len(self.questions)):
            self.add_tab('Question {}'.format(i+1), i)
        self.add_finish()
    
    def initGUI(self):
        self.root = Toplevel(self.masterFrame)
        self.root.wm_title(self.title)
        self.root.bind("<Button-1>", self.get_left_click)
        self.root.bind("<Button-2>", self.get_right_click)

        self.geom_x = 550
        self.geom_y = 200
        self.root.geometry("{}x{}".format(self.geom_x, self.geom_y))

        self.notebook = ttk.Notebook(self.root)
        # result
        self.result = []
        self.dataDict = OrderedDict()
        # variables
        self.variables = {}

        for i, v in enumerate(self.questions):
            if v[0] == "textInput":
                self.variables[i] = StringVar()
                self.variables[i].set("")
            else:
                self.variables[i] = IntVar()
                self.variables[i].set(999)

        self.progval = IntVar()
        self.confirmLabel = None
        self.pos = 0

        # style
        self.style = ttk.Style()
#         print self.style.theme_names()
#         ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
        self.style.theme_use('xpnative')

#         self.style.configure("blue.Horizontal.TProgressbar", background='black')
        self.style.configure('TNotebook.Tab', padding=(12, 8, 12, 0))

        # get max entries in all possible answers (for GUI design)
        tuples = [(i, len(self.questions[i][2])) for i in range(len(self.questions)) if self.questions[i][2]]
        self.max_columns = max(tuples, key=lambda x: x[1])[1]
    

        
    def add_start(self):
        """add start widget"""
        frameStart = ttk.Frame(self.notebook)
        self.notebook.add(frameStart,text="start")

        label = ttk.Label(frameStart, text="This will be the beginning of questionnaire", font=('arial', 12, 'bold'),
                          style="BW.TLabel")
#         label.grid(row=0, column=0, rowspan=4, columnspan=self.max_columns, padx=10, pady=10, sticky=N)
        label.place(relx=.5, rely=.2, anchor="center")

        startButton = ttk.Button(frameStart, text="Start", command=self.start)
#         startButton.grid(row=4, column=0, columnspan=self.max_columns, padx=10, pady=10, sticky=S)
        startButton.place(relx=.5, rely=.5, anchor="center")

        self.notebook.pack(fill=BOTH, expand=1)
#         frameStart.grid_rowconfigure(0, weight=1)
#         frameStart.grid_columnconfigure(0, weight=1)
#         button.bind("<Button-1>", self.get_text)


    def add_tab(self, title, pos):
        """add question widget"""
        # frame and notebook
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame,text=title, state="hidden")

        # question
        label = ttk.Label(frame,text=self.questions[pos][1], font=(12))
        label.grid(row=0, columnspan=self.max_columns, padx=10, pady=10, sticky=N+E+W)

        # radiobutton
        if self.questions[pos][0] == "radioButton":
            for i, question_tuple in enumerate(self.questions[pos][2]):
                val, feature = question_tuple
                b = ttk.Radiobutton(frame, text=feature, variable=self.variables[pos],
                                    value=val, command=lambda: self.get_text())
                b.grid(row=1, column=i, padx=10, pady=10, sticky=E+W)
#                 b.place(relx=float("0.{}".format(i*2)), rely=.5, anchor="center")

        # scale (slider)
        elif self.questions[pos][0] == "scale":
            self.variables[pos].set(0)
            s = Scale(frame, orient=HORIZONTAL, from_=0, to=100, length=self.geom_x * .5,
                          tickinterval=10, variable=self.variables[pos], command=self.get_scale)
            s.grid(row=1, column=0, padx=10, pady=1)

        # text entry
        elif self.questions[pos][0] == "textInput":
            t = ttk.Entry(frame, width=30, textvariable=self.variables[pos])
            t.grid(row=1, column=0, padx=10, pady=10, sticky=W)
            # put blinking cursor inside entry box
            t.focus()
            # comment this if you don't want to have text input stored with keypress "enter"
            t.bind("<Return>", self.get_text)

        # progress bar
        self.progress = ttk.Progressbar(frame, orient="horizontal", value=0, maximum=len(self.questions),
                                        variable=self.progval, length=200, mode="determinate",
                                        style='black.Horizontal.TProgressbar')
        self.progress.place(relx=0.5, rely=0.9, anchor="center")

        # forward and backward buttons
        forward = ttk.Button(frame, text=">>", command=self.next_page)
        forward.place(relx=.9, rely=.9, anchor="center")
        backward = ttk.Button(frame, text="<<", command=self.previous_page)
        backward.place(relx=.1, rely=.9, anchor="center")

        self.notebook.pack(fill=BOTH, expand=1)


    def add_finish(self):
        """add finish widget"""
        frameEnd = ttk.Frame(self.notebook)
        self.notebook.add(frameEnd,text="End", state="hidden")

        label = ttk.Label(frameEnd, text="Thank you for your cooperation", style="BW.TLabel")
        label.place(relx=.5, rely=.2, anchor="center")

        endButton = ttk.Button(frameEnd, text="Finish", command=self.finish)
        endButton.place(relx=.5, rely=.5, anchor="center")

        backward = ttk.Button(frameEnd, text="<<", command=self.previous_page)
        backward.place(relx=.1, rely=.9, anchor="center")

        self.notebook.pack(fill=BOTH, expand=1)


    def start(self):
        """procedure at beginning of questionnaire"""
        # store starting time
        #self.result["timeStamp"] = "User started questionnaire"
        self.startTime = datetime.now() 
        self.dataDict["timeStamp"] = self.startTime
        self.dataDict["action"] = "QuestionnaireStarted"
#        self.saveDataDictToDB()
        # make widget inaccessible
        self.notebook.tab(self.notebook.select(), state="hidden")
        # move focus to next widget
        self.notebook.select(1)


    def check_variable(self):
        """check if user has filled required fields"""
        returnResult = False
        if int(self.questions[self.pos][-1]) == 1:
            if isinstance(self.variables[self.pos].get(), str):
                if len(self.variables[self.pos].get()) == 0:
                    returnResult = True
#                else:
                    # if a user returns to this text entry (with back button), create new timestamp in dictionary
                    #self.result[time.time()] = [self.get_tab_name(), self.variables[self.pos].get()]

            else:
                if self.variables[self.pos].get() == 999:
                    returnResult = True
                    
        self.dataDict["timeStamp"] = datetime.now()
        self.dataDict["question"] = self.get_tab_name()
        self.dataDict["answer"] = self.variables[self.pos].get() #or position
#        self.saveDataDictToDB()
        
        return returnResult

    def post_warning(self, current_page, warningText):
        """place a warning to currently opened tab notebook tab"""
        # get corresponding frame
        frame = self.notebook.winfo_children()[current_page]
        # set label
        self.confirmLabel = ttk.Label(frame, text=warningText, font=(9))
        self.confirmLabel.grid(row=2, columnspan=self.max_columns, padx=10, pady=10, sticky=N+E+W)

    def next_page(self):
        """move to next page"""
        # get page that the focus is on
        current_page = self.notebook.index(self.notebook.select())

        if self.check_variable():
            self.post_warning(current_page, "Please answer, the answer is required")

        else:
            # move to next page
            self.notebook.select(current_page + 1)

            # after moving, hide current page
            self.notebook.tab(current_page, state="hidden")

            # store timestamp
            self.dataDict["timeStamp"] = datetime.now()
            self.dataDict["action"] = "MovedToPage"
            self.dataDict["value"] = current_page + 1 #pageNumber
#            self.saveDataDictToDB()
            #self.result[time.time()] = "User moved to page {}".format(current_page + 1)

            # get progress value and increment
            current_progress = self.progress["value"]
            self.progval.set(current_progress + 1)

            # clean confirm label
            if self.confirmLabel:
                self.confirmLabel.grid_forget()

            # pos = current_page because questions start at 0 and page at 1
            # otherwise it would be pos = current_page + 1
            self.pos = current_page


    def previous_page(self):
        """move to previous page"""
        # get current page
        current_page = self.notebook.index(self.notebook.select())

        if current_page != 1:
            # move to previous page and hide current
            self.notebook.select(current_page - 1)
            self.notebook.tab(current_page, state="hidden")
            # store result
            #self.result[time.time()] = "User moved to page {}".format(current_page - 1)
            self.dataDict["timeStamp"] = datetime.now()
            self.dataDict["action"] = "MovedToPage"
            self.dataDict["value"] = current_page - 1 #pageNumber
#            self.saveDataDictToDB()
            # get progress value
            current_progress = self.progress["value"]
            # decrease progress value
            self.progval.set(current_progress - 1)
            # - 2 because pages start from 1 and qustions start from 0
            # otherwise it would be current_page - 1
            self.pos = current_page - 2


    def run(self):
        """run root object in loop"""
        #self.root.mainloop()
        pass # since it is opened as apop up window it is seen when packed. 


    def finish(self):
        """finish procedure"""
        #self.result[time.time()] = "User completed questionnaire"
        self.dataDict["timeStamp"] = datetime.now()
        self.dataDict["action"] = "QuestionnaireCompleted"
        
        self.logger.debug("Close questionnaire {}".format(self.filename))
        
        if self.nextActTrig:
            self.queue.put(datetime.now())
        
#        self.saveDataDictToDB()
        #compute the final answers and save to DB
#        self.computeAndSaveFinalAnswersToDB()
        self.root.destroy()


    def get_scale(self, curr_scale):
        """get values from slider"""
        #self.result[time.time()] = [self.get_tab_name(), curr_scale]
        self.dataDict["timeStamp"] = datetime.now()
        self.dataDict["action"] = "SliderMoved"
        self.dataDict["question"] = self.get_tab_name()
        self.dataDict["answer"] = self.variables[self.pos].get()#curr_scale
#        self.saveDataDictToDB()


    def get_text(self, event=None):
        """get text value"""
        #self.result[time.time()] = [self.get_tab_name(), self.variables[self.pos].get()]
        self.dataDict["timeStamp"] = datetime.now()
        self.dataDict["action"] = "TextInput"
        self.dataDict["question"] = self.get_tab_name()
        self.dataDict["answer"] = self.variables[self.pos].get()
#        self.saveDataDictToDB()


    def get_tab_name(self):
        # get name of the tab
        current_page = self.notebook.index(self.notebook.select())
        return self.notebook.tab(current_page)['text']


    def get_left_click(self, event):
        x, y = event.x, event.y
        #self.result[time.time()] = ["Left Click Position", (x, y)]
        self.dataDict["timeStamp"] = datetime.now()
        self.dataDict["action"] = "LeftClick"
        self.dataDict["value:x"] = x
        self.dataDict["value:y"] = y
#        self.saveDataDictToDB()


    def get_right_click(self, event):
        x, y = event.x, event.y
        #self.result[time.time()] = ["Right Click Position", (x, y)]
        self.dataDict["timeStamp"] = datetime.now()
        self.dataDict["action"] = "RightClick"
        self.dataDict["value:x"] = x
        self.dataDict["value:y"] = y
#        self.saveDataDictToDB()
    
#    def saveDataDictToDB(self):
#        """
#        saves local dataDict to db and clears it
#        """
#        self.dataDict["questionnaireType"] = self.questType
#        Database.saveToDB(self.dbSectionName, self.dataDict)
#        copDataDict = OrderedDict(self.dataDict)
#        self.result.append(copDataDict)
#        self.dataDict.clear()
#        
#    def computeAndSaveFinalAnswersToDB(self):
#        """
#        Save final answers to the questions in the finalanswerscollection for easy using later for analysis
#        """
#        #before closing the questionnaire filter the result dict for only questions
#        filteredResult = list(filter(lambda d: "question" in d, self.result))
#                
#        #before closing the questionnaire get the final answers for each question, whose relativeTime is max
#        finalQuestionAndAnswers = []
#        for key, group in groupby(filteredResult, lambda x: x["question"]): 
#            finalQuestionAndAnswers.append(max(group, key=lambda x:x["timeStamp"]))
#        
#        #['type', 'questionText', 'possibleAnswer', 'required']
#        #since two sets are ordered assign question description to questions                
#        for item,eachQuestion in izip(finalQuestionAndAnswers, self.questions):
#            for index in range(0, len(self.questionnaireConf)):
#                item[self.questionnaireConf[index]] = eachQuestion[index]
#                        
#        #change answer key to final answer in order not to be mixed with original data
#        for item in finalQuestionAndAnswers:
#            item["questionnaireType"] = self.questType
#            Database.saveToDB("QUESTIONNAIRE", item, self.finalAnswersCollectionName)
