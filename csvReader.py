# -*- coding: utf-8 -*-
"""
Created on Fri May 25 11:26:22 2018

@author: Nejc Kozjek
"""

import csv

class csvReader:
    
    def __init__(self, filepath, delimiter):
        self.filepath = filepath
        self.delimiter = delimiter
        self.questionnaire = []


    def load_csv(self):
        with open(self.filepath, "rb") as f_read:
            reader = csv.reader(f_read, delimiter=self.delimiter)
            # skip first line which is a header
            self.questionnaireConf = next(reader, None)
            
            # traverse lines and store
            for row in reader:
                self.questionnaire.append(row)


    def clean_questionnaire(self):
        for i, item in enumerate(self.questionnaire):
            if item[2]:
                self.questionnaire[i][2] = eval(item[2])


    def make_questions(self):
        self.load_csv()
        self.clean_questionnaire()
        return self.questionnaire
    
    def getQuestionnaireConf(self):
        return self.questionnaireConf