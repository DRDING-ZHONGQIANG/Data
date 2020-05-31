# -*- coding: utf-8 -*-
"""
Created on Tue May 12 11:30:14 2020

@author: balian
"""
import os
import numpy as np
import datetime
import time
import pandas as pd
import dateutil.parser
import pytz

class dist_plot:
    
  @classmethod  
  def __init__(self, directory):
    self.directory = directory 
    now_timestamp = time.time()
    self.offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
    
  def get_timestamp(self,filename):
    file_preprocessing1 = filename.replace('fish','')
    file_preprocessing1 = file_preprocessing1.replace('.csv','')
   # file_preprocessing1 = file_preprocessing1.remove('')
    year   = file_preprocessing1[0:4]
    month  = file_preprocessing1[4:6]
    day    = file_preprocessing1[6:8]
    hour   = file_preprocessing1[8:10]
    minute = file_preprocessing1[10:12] 
    second = file_preprocessing1[12:14]
    timestring = day +'/' + month +'/' + year + ' ' + hour + ':' + minute + ':' + second
    datetimeObj = datetime.datetime.strptime(timestring, '%d/%m/%Y %H:%M:%S')      
    return datetimeObj       
    
  def dict_singlefile(self,filename): 
    data = np.array(pd.read_csv(os.path.join(self.directory,filename)))    
    cIndex_a  = data[:,2]
    speed_a   = data[:,3] 
    cIndex    = np.mean(cIndex_a)     
    speed     = np.mean(speed_a)
    timestamp = self.get_timestamp(filename)     
    row =[timestamp, cIndex, speed]    
    return row   
   
  def dict_water(self, directory, filename):
    data = np.array(pd.read_csv(os.path.join(directory,filename)))  
    return data

  def run_app(self):    
    list = []  
    for file in os.listdir(self.directory):           
            list.append( self.dict_singlefile(file))    
    return list

  # vdata is a list of object 
  def find_vValue(self, wtime, vdata):      
     cIndex = 0
     fSpeed = 0    
     rows = vdata.shape[0]        
     for i in range(rows):      
         timeins = vdata[i,0]
         time2   = pytz.utc.localize(timeins)
         if (wtime == time2):
            cIndex = vdata[i,1]
            fSpeed = vdata[i,2]
            break
         if (wtime > time2):
            tdifference = wtime - time2
            delta = tdifference.days * 24*60 +  tdifference.seconds/24
            if (delta < 6  ):
                cIndex = vdata[i,1]
                fSpeed = vdata[i,2]
                break                       
         if (wtime < time2): 
            cIndex = vdata[i,1]
            fSpeed = vdata[i,2] 
            break       
     return cIndex, fSpeed
 
  def merge(self, vdata, wdata):    
      rows = wdata.shape[1]    
      y = np.zeros((rows, 5)).astype(object)
      wdata1 = wdata[0]
      for i in range(rows):          
          element_list = wdata1[i]
          wtime = element_list[1]
          wtime =  dateutil.parser.parse(wtime)  
          wtime =  wtime + self.offset
          [cI, fd] = self.find_vValue(wtime, np.array(vdata))          
          y[i, 0] = element_list[0]
          wtime = wtime.replace(tzinfo=None)
          y[i, 1] = wtime.timestamp()
          y[i, 2] = element_list[3]
          y[i, 3] = cI
          y[i, 4] = fd           
      return y
      
if __name__ == '__main__':
     
    videodata = []
    waterdata = []
    
    directory = r'd:/data/week3/day1'
    dp = dist_plot(directory)      
    vd = dp.run_app()
    videodata = vd
    
    directory = r'd:/data/week3/day2'
    dp = dist_plot(directory)      
    vd = dp.run_app()
    videodata = videodata + vd
    
    directory = r'd:/data/week3/day3'
    dp = dist_plot(directory)      
    vd = dp.run_app()
    videodata = videodata + vd

    directory = r'd:/data/week3/day4'
    dp = dist_plot(directory)      
    vd = dp.run_app()
    videodata = videodata + vd

    wd = dp.dict_water(r'd:/data/week3','week3.csv')
    waterdata.append(wd)

    data = dp.merge(videodata, np.array(waterdata))
    data = data[::-1]
    df = pd.DataFrame(data)
    df.to_csv(r'D:/data/week3/week3_rst.csv')
    
    
    
    
    
    
    
    
    
    