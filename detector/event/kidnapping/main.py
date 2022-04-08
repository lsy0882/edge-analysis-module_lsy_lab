from collections import OrderedDict

import os
import time
import numpy as np

from itertools import combinations, product
from detector.event.template.main import Event

def boxOverlapCheck(coord1, coord2, type):

    if type == 2:
        if (coord1[2] * coord1[3]) >= (coord2[2] * coord2[3]):
            return 0
    elif type == 1:
        p1 = coord1[2] * coord1[3] # y*w
        p2 = coord2[2] * coord2[3] # y*w
        if p1 != p2:
            if p1 > p2:
                bigger = p1
                smaller = p2
            else :
                bigger = p2
                smaller = p1                
            if bigger > 3 * smaller:
                return 0

    coord = []
    coord.append(coord1)
    coord.append(coord2)
    eventFlag = 0
    for target in range(2):
        targetCoord = []
        targetCoord = ((coord[target][0], coord[target][1]), ### (x,y)
            (coord[target][0], coord[target][1] + coord[target][3]), ### (x, y+h)
            (coord[target][0] + coord[target][2], coord[target][1]), ### (x+w, y)
            (coord[target][0] + coord[target][2], coord[target][1] + coord[target][3])) ### (x+w, y+h)
        if target < 1 :
            other = 1
        else :
            other = 0
        for i in range(4): 
            if targetCoord[i][0] >= coord[other][0] and targetCoord[i][0] <= (coord[other][0] + coord[other][2]):
                if targetCoord[i][1] >= coord[other][1] and targetCoord[i][1] <= (coord[other][1] + coord[other][3]):
                    eventFlag = 1

    return eventFlag

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

    def inference(self, frame, detection_result):
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        ret = 0
        boxOverlapFlag = 0
        detected_person, detected_vehicles = [], []
        for i, e in enumerate(detection_result['results'][0]['detection_result']):
            if e['label'][0]['description'] in ['person'] and e['label'][0]['score'] > 0.65 and (e['position']['w'] < e['position']['h']) and (e['position']['w'] / e['position']['h'])<0.9:
             
                detected_person.append(
                    (e['position']['x'], e['position']['y'], e['position']['w'], e['position']['h'])
                    )
        for i, e in enumerate(detection_result['results'][0]['detection_result']):
            if e['label'][0]['description'] in ['car'] and e['label'][0]['score'] > 0.5:
          
                detected_vehicles.append(
                    (e['position']['x'], e['position']['y'], e['position']['w'], e['position']['h'])
                    )                    
        num_of_person = len(detected_person)
        num_of_vehicles = len(detected_vehicles)

        combi, target = [], []
        if num_of_person >= 2 and num_of_person <= 4 and num_of_vehicles >= 1: ### 보행자가 2인 이상, 차량이 1개 이상 검출
            pair_of_person_coordinates = np.array(list(combinations(detected_person, 2)), dtype=int)
            if len(pair_of_person_coordinates) >= 1:
                for i in range(len(pair_of_person_coordinates)) :
                    boxOverlapFlag = boxOverlapCheck(pair_of_person_coordinates[i][0], pair_of_person_coordinates[i][1], type=1)
                    if boxOverlapFlag == 1:
                        combi.append(pair_of_person_coordinates[i][0])
                        combi.append(pair_of_person_coordinates[i][1])
            if len(combi) >= 1:
                pair_of_coordinates = np.array(list(product(combi, detected_vehicles)), dtype=int)
                if len(pair_of_coordinates) >= 1 :
                    for i in range(len(pair_of_coordinates)) :
                        boxOverlapFlag = boxOverlapCheck(pair_of_coordinates[i][0], pair_of_coordinates[i][1], type=2)
                        if boxOverlapFlag == 1:
                            ret = 1


        
        
        if len(self.history) == 80 :
            self.history.pop(0)

        self.history.append(ret)

        if sum(self.history) >= 2 :
            self.result = True
        else :
            self.result = False

        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        return self.result