from __future__ import print_function
import os
import numpy as np
import json
import time

class FalldownDetection:
    model = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        self.model_name = "FalldownDetection"
        self.people_max = 100
        
        # print(self.model_name)
        self.analysis_time = 0
        #self.debug = debug        
        self.history = []
        for i in range(self.people_max):
            self.history.append(0)

        self.result = [] 
             
        self.people_locate = []
        for i in range(self.people_max):
            self.people_locate.append([0,0])
        
        self.temp_frame =1
        self.stop_count = 0

    def analysis_from_json(self, od_result):

        # rule 1  
        count = 0
        detection_result = od_result['results'][0]['detection_result']
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
                    
                
                for i in range(self.people_max):
                    dis_x = self.people_locate[i][0] - int(info_['position']['x'])
                    dis_y = self.people_locate[i][1] - int(info_['position']['y'])
                    
                    if (dis_x*dis_x) + (dis_y*dis_y) < 10\
                        and int(info_['position']['w']) >= int(info_['position']['h']):
                        self.history[i] += 1
                        break # if checked the info_['position'], break and check other person
                        
                    elif self.history[i] > 0 : 
                        self.history[i] -= 1
                
                
                self.people_locate[count] = [int(info_['position']['x']), int(info_['position']['y'])]

                count += 1 # person count      
                
        #print("history : ", self.history)
        
        self.result = 0 #init 
        for i in range(self.people_max):
            if self.history[i] > 10:
                #print("Fall down!, ", self.people_locate[i])
                self.result = 1
        
        
        return self.result
