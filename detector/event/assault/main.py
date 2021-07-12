import os
import time
import itertools
import numpy as np
from detector.event.template.main import Event
from PIL import Image


class AssaultEvent(Event):
    model = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False):
        super().__init__(debug)
        self.model_name = "assault"
        self.history = []
        self.debug = debug
        self.result = 0
        self.analysis_time = 0
        self.distance_sum = []
        self.prev_frame = []
        self.frame_count = 0

    def inference(self, frame_info, detection_result):
        frame = frame_info["frame"]
        frame_number = frame_info["frame_number"]
        pix_sum = np.sum(frame)
        pix_sum = pix_sum/(frame.size)
        self.frame_count = self.frame_count + 1
        self.result = "safe"
        start = 0
        end = 0

        if self.frame_count == 1:
            self.prev_frame.append(-1)

        if self.debug :
            start = time.time()

        if len(self.history) >= 10000:
            self.history = []

        position_list = []
        dist_list = []
        dist_flag = 0
        dist_ = 99999999

        detection_result = detection_result['results'][0]['detection_result']  
        person_num = 0
        for info_ in detection_result:

            if info_['label'][0]['description'] == 'person' and info_['label'][0]['score'] > 0.5:
                person_num = person_num + 1
                if info_['position']['w'] > 0 and info_['position']['h'] > 0:
                  pt_ = np.asarray([info_['position']['x'] + info_['position']['w'] / 2,
                                    info_['position']['y'] + info_['position']['h'] / 2])
                  position_list.append(pt_)

        combinations_ = list(itertools.combinations(position_list, 2))

        dist_sum = 0

        for pt_ in combinations_:
            dist_ = np.linalg.norm(pt_[0] - pt_[1])
            dist_list.append(dist_)

            dist_sum = dist_sum + dist_
            frame_dist = abs(sum(self.distance_sum[-1:]) - dist_sum)

            self.distance_sum.append(dist_sum)
    
        self.result = False

        if person_num > 4:
            self.history.append(0)
            self.result = False
            self.prev_frame = []
            self.prev_frame.append(-1)
            return self.result

        else:
         if person_num > 1:
              velo = []
              dist_list = []

              if self.prev_frame[0] != -1:
                
                 prev_person_num = self.prev_frame[0]
            
                 if prev_person_num <= person_num:
                     for i in range (prev_person_num):
                         for j in range(person_num):
                             co = []

                             x_co = detection_result[j]['position']['x'] + detection_result[j]['position']['w'] / 2
                             y_co = detection_result[j]['position']['y'] + detection_result[j]['position']['h'] / 2
                            
                             
                             width_len = abs(x_co - self.prev_frame[i+1][0])
                             height_len = abs(y_co - self.prev_frame[i+1][1])
                             co.append(x_co)
                             co.append(y_co)
                             tans = height_len/width_len
                             mus = ((4*tans*tans)+4)/(4+(tans*tans))
                             mus = np.sqrt(mus)
                             
                             dist_list.append(mus*(np.linalg.norm(self.prev_frame[i+1] - co)))

                         if person_num != 0 and prev_person_num != 0:
                            velo.append(min(dist_list))
                            dist_list = []
                         else:
                             dist_list = []
                             velo=[]

                 elif prev_person_num > person_num: 
                     for i in range (person_num):
                         co2 = []
                         x_co = detection_result[i]['position']['x'] + detection_result[i]['position']['w'] / 2
                         y_co = detection_result[i]['position']['y'] + detection_result[i]['position']['h'] / 2
                         co2.append(x_co)
                         co2.append(y_co)
  
                         for j in range (prev_person_num):
                              width_len = abs(x_co - self.prev_frame[j+1][0])               
                              height_len = abs(y_co - self.prev_frame[j+1][1]) 
                              tans = height_len/width_len
                              mus = ((4*tans*tans)+4)/(4+(tans*tans))                      
                              mus = np.sqrt(mus) 
                              dist_list.append(mus*np.linalg.norm(self.prev_frame[j+1] - co2))
                         if person_num != 0 and prev_person_num != 0:
                             velo.append(min(dist_list))
                         else:
                             velo=[]
                             
              velo_count = 0
              velo_thres = 50

              for i in range (len(velo)):
                  if velo[i] >= velo_thres:
                     velo_count = velo_count + 1

              if len(velo) == 2 or len(velo) == 3:
                  if velo_count >= 2:
                      velo_count = 0
                      self.history.append(0)
                      self.result = False
                      return self.result
              
              elif len(velo) == 4:
                   if velo_count >= 3:
                      velo_count = 0
                      self.history.append(0)
                      self.result = False
                      return self.result
                
              velo = []
              self.prev_frame = []
              self.prev_frame.append(person_num)

              for i in range (person_num):
                  pos_np = np.asarray([detection_result[i]['position']['x'] + detection_result[i]['position']['w'] / 2 , detection_result[i]['position']['y'] + detection_result[i]['position']['h'] / 2])
                  self.prev_frame.append(pos_np) 


        #if person_num > 4:
       # print("\naaaa")
       # print(self.prev_frame)
          
        # Rule 1) If two people are close to each other
        if dist_list:
            for dist_ in dist_list:
                if dist_ < 40:
                 # if frame_dist > 3:
                    self.history.append(1)  # return true
                    self.result = True
                    return self.result
                       
        #dist_thres =  (bbox_size_avg/100) * dist_sum

        # Rule 2) Simple smoothing
        if sum(self.history[-60:]) > 3:
         # if self.history[-3:] == True and self.history[-2:] == True and self.history[-1:] == True:
            self.history.append(0)
            self.result = True
            return self.result

        self.history.append(0)
        self.result = False
    

        if self.debug :
            end = time.time()
            self.analysis_time = end - start


        return self.result
