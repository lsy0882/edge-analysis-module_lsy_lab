from __future__ import print_function
import os
import numpy as np
import json
import time

class FalldownDetection:
    model = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug):
        self.model_name = "FalldownDetection"
        self.people_max = 100
        
        # print(self.model_name)
        self.analysis_time = 0
        self.debug = debug        
        self.history = []
        for i in range(self.people_max):
            self.history.append(0)

        self.result = [] 
             
        self.people_locate = []
        for i in range(self.people_max):
            self.people_locate.append([0,0])
        
        self.temp_frame =1
        self.stop_count = 0
        self.tracking_method = False
        self.before_falldown_count = [0 for i in range (self.people_max)]

    def analysis_from_json(self, od_result):
        start = 0
        end = 0

        if self.debug :
            start = time.time()

        # rule 1  
        count = 0
        detection_result = od_result['results'][0]['detection_result']
        self.result = 0 #init 
            
        for info_ in detection_result:
            #print(info_['position'])
            #dets =[]
            if info_['label'][0]['description'] == "person" and float(info_['label'][0]['score']) > 0.5:
                #dets.append(int(info_['position']['x']))
                #dets.append(int(info_['position']['y']))
                #dets.append(int(info_['position']['x']+info_['position']['w']))
                #dets.append(int(info_['position']['y']+info_['position']['h']))
                #convert to [x1,y1,w,h] to [x1,y1,x2,y2]
                #dets.append(float(info_['label'][0]['score']))

                #print("x: , ", int(info_['position']['x']) , " y: ",int(info_['position']['y']) )  
                        
                
                if self.tracking_method == True:
                
                    for i in range(self.people_max):
                        dis_x = self.people_locate[i][0] - int(info_['position']['x'])
                        dis_y = self.people_locate[i][1] - int(info_['position']['y'])
                        
                        if (dis_x*dis_x) + (dis_y*dis_y) < 100\
                            and int(info_['position']['w']) >= int(info_['position']['h']):
                            self.history[i] += 1
                            break # if checked the info_['position'], break and check other person
                            
                        elif self.history[i] > 0 : 
                            self.history[i] -= 1
                    
                    
                    self.people_locate[count] = [int(info_['position']['x']), int(info_['position']['y'])]
                    
                else:
                    if int(info_['position']['w']) >= int(info_['position']['h']):
                        self.before_falldown_count[count] += 1
                    else :
                        self.before_falldown_count[count] = 0
                        
                    #print("before_falldown_count : ", self.before_falldown_count[count])
                    
                count += 1 # person count 
                
        #print("history : ", self.history)
        
        if self.tracking_method == True:
            for i in range(self.people_max):
                if self.history[i] > 3:
                    #print("Fall down!, ", self.people_locate[i])
                    self.result = 1
        else:
            for i in range(self.people_max):
                if self.before_falldown_count[i] >1 :
                    #print("Fall down!, ", self.before_falldown_count[i])
                    self.result = 1
                    break
        #print("self.result :", self.result )    
        
        if self.debug :
            end = time.time()
            self.analysis_time = end - start
        
        return self.result
