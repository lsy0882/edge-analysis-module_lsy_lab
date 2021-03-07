from __future__ import print_function
import os
import numpy as np
import json
import time

from detector.event.wanderer.utils import *
from detector.event.wanderer.Sort import Sort

np.random.seed(0)


class WanderDetection:
    model = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False):
        self.model_name = "wanderer"
        self.analysis_time = 0
        self.debug = debug
        self.history = []
        self.result = 0


    def analysis_from_json(self, od_result):
        frame = od_result["frame_number"]
        # frame = frame_n
        # print(frame)
        start = 0
        end = 0
        if self.debug :
            start = time.time()


        od_result = od_result.decode('utf-8').replace("'", '"')
        od_result = json.loads(od_result)
        
        # frame = od_result["frame_number"]
        # print("frame: {}".format(frame))
        detection_result = od_result["results"][0]["detection_result"]
        result = {}
        det_list = []
        # print(detection_result)
        for info_ in detection_result:
            # print(info_['position'])
            dets =[]
            if info_['label'][0]['description'] == "person":
                dets.append(int(info_['position']['x']))
                dets.append(int(info_['position']['y']))
                dets.append(int(info_['position']['x']+info_['position']['w']))
                dets.append(int(info_['position']['y']+info_['position']['h']))
                #convert to [x1,y1,w,h] to [x1,y1,x2,y2]
                dets.append(float(info_['label'][0]['score']))
                det_list.append(dets)

        trackers = self.mot_tracker.update(det_list) # output : track_id, x1,y1,x2,y2
        # print('%d,%d,%.2f,%.2f,%.2f,%.2f'%(frame,trackers[4],trackers[0],trackers[1],trackers[2]-trackers[0],trackers[3]-trackers[1]))
        # print(trackers[:,4])
        # rule 1 
        self.result = 0
        for d in trackers:
            while len(self.id_stack) <= d[4]:
                self.id_stack.append(0)
            # previous_id_stack = copy.deepcopy(self.id_stack)
            
            self.id_stack[int(d[4])] +=1
            # detect Wander
            if self.id_stack[int(d[4])] >= 20:        
              # if previous_id_stack[int(d[4])]!=self.id_stack[int(d[4])]:
              result["event"] ="wander"
              result["frame"] = int(frame)
              result["id_num"] = int(d[4])
              result["id_count"] = self.id_stack[int(d[4])]
              # print("wander frame : {}, id_num : {}, id_count {}".format(frame,int(d[4]), self.id_stack[int(d[4])]))
              self.history.append(result)
              self.result = 1
        
        return self.result
