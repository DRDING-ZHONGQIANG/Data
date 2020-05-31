# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:28:13 2020

@author: A101297
"""
import datetime
import os
from os import path

def process1(directory):
       count = 1
       print('[')
       print(count)
       print('],')
       for filename in os.listdir(directory):
        if filename.endswith(".avi") :            
             count = count + 1
             print('[')
             print(count)
             print('],')
             fullpath = os.path.join(directory, filename)
             print(fullpath)  
             cmdpath = 'python run.py -s ' + fullpath 
             new_name = filename.replace('avi','csv')
             if path.exists( os.path.join(directory, new_name)):
                 pass
             else:            
                 now = datetime.datetime.now()
                 print (now.strftime("%Y-%m-%d %H:%M:%S"))
                 os.system(cmdpath)
                 os.rename('data.csv', os.path.join(directory, new_name)) 
        else:
                continue

print('week1')
directory = r'D:\data\Week2\day3'
process1(directory)

print('week2')
directory = r'D:\data\Week2\day4'
process1(directory)

#directory =  r'D:\data\Week1\day3'
#process1(directory)

#directory =  r'D:\data\Week1\day4'
#process1(directory) 