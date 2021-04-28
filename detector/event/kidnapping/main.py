from collections import OrderedDict

import os
import json
import time
import numpy as np
import math
from itertools import combinations
from detector.event.template.main import Event

class KidnappingEvent(Event):
    model = None
    result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False):
        super().__init__(debug)
        self.model_name = "kidnapping"
        self.analysis_time = 0
        self.debug = debug
        self.history = []
        self.max_history = 10
        self.frame = None
        
    def inference(self, frame, detection_result):
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        eventFlag = 0
        result = OrderedDict()
        detected_person = []
        for i, e in enumerate(detection_result['results'][0]['detection_result']):
            if e['label'][0]['description'] in ['person']:
                detected_person.append(
                    ((e['position']['x'] + e['position']['w'] / 2), (e['position']['y'] + e['position']['h'] / 2)))

        num_of_person = len(detected_person)

        result["num_of_person"] = num_of_person
        result["center_coordinates"] = detected_person

        # kidnapping detection module
        if num_of_person >= 2 :
            self.pre_detected_person = num_of_person
            pair_of_center_coordinates = np.array(list(combinations(detected_person, 2)), dtype=int)
            if len(pair_of_center_coordinates) >= 1 :
                for i in range(len(pair_of_center_coordinates)) :
                    dist = np.linalg.norm(pair_of_center_coordinates[i][0] - pair_of_center_coordinates[i][1])
                    if dist < 100 :
                        eventFlag = 1
            

        if len(self.history) >= self.max_history :
            self.history.pop(0)
        self.history.append(eventFlag)

        # Smoothing (history check)
        sum = 0
        if len(self.history) == self.max_history :
            for i in range(self.max_history) :
                if self.history[i] == 1 :
                    sum += 1

        if sum >= (self.max_history * 0.6):
            if self.history[7] == 1 and self.history[8] == 1 and self.history[9] == 1:
                state = True
            else:
                state = False
        else :
            state = False

        self.result = state


        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        return self.result
