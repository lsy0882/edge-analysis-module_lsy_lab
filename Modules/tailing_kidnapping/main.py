from collections import OrderedDict

import os
import json
import time
import numpy as np
from itertools import combinations

class Tailing_Kidnapping:
    model = None
    result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug):
        self.model_name = "Tailing_Kidnapping"
        self.analysis_time = 0
        self.debug = debug
        self.history = []
        self.history_state = []
        self.max_history = 10
        self.warning = 0

    def analysis_from_json(self, od_result):
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        received = od_result.decode('utf-8').replace("'", '"')
        data = json.loads(received)

        result = OrderedDict()
        detected_person = []
        detected_vehicle = []

        result["frame_num"] = data["frame_num"]

        for i, e in enumerate(data['results'][0]['detection_result']):
            if e['label'][0]['description'] in ['person']:
                person = OrderedDict()
                # person["id"] = i+1  # id는 1부터 시작
                person["position"] = e['position']
                person["center_coordinates"] =  ( (e['position']['x'] + e['position']['w'])/2, (e['position']['y'] + e['position']['h'])/2 )
                detected_person.append(person)
            elif e['label'][0]['description'] in ['car', 'truck']:
                vehicle = OrderedDict()
                vehicle["position"] = e['position']
                vehicle["center_coordinates"] = ( (e['position']['x'] + e['position']['w'])/2, (e['position']['y'] + e['position']['h'])/2 )
                detected_vehicle.append(vehicle)

        num_of_detected_person = len(detected_person)
        num_of_detected_vehicle = len(detected_vehicle)

        # result["detected_person"] = num_of_detected_person
        result["adjacnency"] = None

        if num_of_detected_person >=2 and num_of_detected_person <= 4 : # 보행자가 2~4인 
            center_coordinates = []
            for i in range(num_of_detected_person):
                center_coordinates.append(detected_person[i]["center_coordinates"])

            pair_of_center_coordinates = np.array(list(combinations(center_coordinates, 2)), dtype=int)

            dist = 0
            set_of_adjacency = []
            for i in range(pair_of_center_coordinates.shape[0]):
                adjacency = OrderedDict()
                dist = np.linalg.norm(pair_of_center_coordinates[i][0] - pair_of_center_coordinates[i][1])
                if dist < 20 :
                    adjacency["distance"] = dist
                    adjacency["between_coordinates"] = (pair_of_center_coordinates[i][0] + pair_of_center_coordinates[i][1])/2
                    set_of_adjacency.append(adjacency)

            result["adjacnency"] = set_of_adjacency

        if len(self.history) >= self.max_history :
            self.history.pop(0)

        self.history.append(result)

        check = 0
        for i in range(len(self.history)) :
            if self.history[i]["adjacnency"] != None :
                check += 1

        prob = check / len(self.history)
        if prob > 0.7 :
            state = 1
        else :
            state = 0

        self.result = state

        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        return self.result