from collections import OrderedDict

import os
import json
import time
import numpy as np
import math
from itertools import combinations

class Tailing_Kidnapping:
    model = None
    result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False):
        self.model_name = "Tailing_Kidnapping"
        self.analysis_time = 0
        self.debug = debug
        self.history = []
        self.max_history = 5
        self.frame = None

    def analysis_from_json(self, od_result):
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        received = od_result.decode('utf-8').replace("'", '"')
        data = json.loads(received)

        eventFlag = 0
        result = OrderedDict()
        detected_person = []
        for i, e in enumerate(data['results'][0]['detection_result']):
            if e['label'][0]['description'] in ['person']:
                detected_person.append(((e['position']['x'] + e['position']['w']/2), (e['position']['y'] + e['position']['h']/2)))

        num_of_person = len(detected_person)

        result["num_of_person"] = num_of_person
        result["center_coordinates"] = detected_person

        # kidnapping detection module
        if num_of_person >= 2 and num_of_person <= 8 :
            pair_of_center_coordinates = np.array(list(combinations(detected_person, 2)), dtype=int)
            if len(pair_of_center_coordinates) >= 1 :
                for i in range(len(pair_of_center_coordinates)) :
                    dist = np.linalg.norm(pair_of_center_coordinates[i][0] - pair_of_center_coordinates[i][1])
                    if dist < 60 :
                        eventFlag = 1

        # tailing detection module
        vector = OrderedDict()
        mapping, tmp_combi = [], []
        if self.frame != None :
            if num_of_person >= 2 and num_of_person <= 8 and self.frame["num_of_person"] > 0 :
                for i in range(num_of_person): # 현재 검출 정보
                    tmp_val = 10000
                    for j in range(self.frame["num_of_person"]): # 이전 프레임 검출 정보
                        dist = math.sqrt( pow(result["center_coordinates"][i][0] - self.frame["center_coordinates"][j][0], 2) + pow(result["center_coordinates"][i][1] - self.frame["center_coordinates"][j][1], 2) )
                        if dist < tmp_val :
                            tmp_val = dist
                            tmp_combi = (result["center_coordinates"][i], self.frame["center_coordinates"][j])
                    mapping.append(tmp_combi)
        
        vector["num_of_mapping"] = len(mapping)
        vector["mapped_coordinates"] = mapping
        
        self.frame = result

        if vector["num_of_mapping"] > 0 :
            tmp_vector = []
            for i in range(vector["num_of_mapping"]) :
                first, last = vector["mapped_coordinates"][i][1], vector["mapped_coordinates"][i][0]
                tmp_vector.append((last[0] - first[0], last[1] - first[1]))
            
            vector["vector"] = tmp_vector
            vector_combi = np.array(list(combinations(vector["vector"], 2)), dtype=float)

            for i in range(vector_combi.shape[0]):
                norm1, norm2 = np.linalg.norm(vector_combi[i][0]), np.linalg.norm(vector_combi[i][1])
                theta = math.acos( float(np.dot(vector_combi[i][0], vector_combi[i][1]) / (norm1 * norm2)) ) 
                deg = (theta * 180) / math.pi
                if deg < 100 :
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
            
        if sum >= (self.max_history * 0.4) :
            state = 1
        else :
            state = 0

        self.result = state

        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        return self.result