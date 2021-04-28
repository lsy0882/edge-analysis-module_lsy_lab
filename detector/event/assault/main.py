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

    def inference(self, frame, detection_result):
        self.result = "safe"
        start = 0
        end = 0

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

        for pt_ in combinations_:
            dist_ = np.linalg.norm(pt_[0] - pt_[1])
            dist_list.append(dist_)

        self.result = False
    
        # Rule 1) If two people are close to each other
        if dist_list:
            for dist_ in dist_list:
                if dist_ < 40:
            
                    self.history.append(1)  # return true
                    self.result = True
                    return self.result

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
