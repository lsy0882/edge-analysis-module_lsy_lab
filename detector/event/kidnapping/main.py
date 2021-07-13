from collections import OrderedDict

import os
import time
import numpy as np
import cv2
import copy

from itertools import combinations, product
from detector.event.template.main import Event

def boxOverlapCheck(coord1, coord2):
    coord = []
    coord.append(coord1)
    coord.append(coord2)
    eventFlag = 0
    for target in range(2):
        targetCoord = []
        targetCoord = ((coord[target][0], coord[target][1]),
            (coord[target][0], coord[target][1] + coord[target][3]),
            (coord[target][0] + coord[target][2], coord[target][1]),
            (coord[target][0] + coord[target][2], coord[target][1] + coord[target][3]))
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
        self.prev_frame = []
        self.target = []

    def opticalFlow(self, frame):

        prvs = cv2.cvtColor(self.prev_frame['frame'], cv2.COLOR_BGR2GRAY)
        next = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(prvs, next, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])

        mag = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        ang = cv2.normalize((ang*180/np.pi/2), None, 0, 255, cv2.NORM_MINMAX)

        grid = np.zeros(shape=(360, 640))
        for i in range(len(self.target)):
            for j in range(self.target[i][3]):
                for k in range(self.target[i][2]):
                    grid[self.target[i][1]+j][self.target[i][0]+k] = 1
                
        mag_sum, activ = 0, 0
        for i in range(360):
            for j in range(640):
                if grid[i][j] == 1:
                    activ += 1
                    mag_sum += mag[i][j]
        
        if activ == 0:
            activ = 1

        return (mag_sum/activ)

    def inference(self, frame, detection_result):
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        if frame['frame_number'] % 5 == 1:
            self.prev_frame = copy.deepcopy(frame)

        boxOverlapFlag = 0
        detected_person, detected_vehicles = [], []
        for i, e in enumerate(detection_result['results'][0]['detection_result']):
            if e['label'][0]['description'] in ['person'] and e['label'][0]['score'] > 0.8:
                detected_person.append(
                    (e['position']['x'], e['position']['y'], e['position']['w'], e['position']['h'])
                    )
        for i, e in enumerate(detection_result['results'][0]['detection_result']):
            if e['label'][0]['description'] in ['car'] and e['label'][0]['score'] > 0.8:
                detected_vehicles.append(
                    (e['position']['x'], e['position']['y'], e['position']['w'], e['position']['h'])
                    )                    
        num_of_person = len(detected_person)
        num_of_vehicles = len(detected_vehicles)

        if num_of_person >= 2 and num_of_person <= 6 and num_of_vehicles >= 1:
            pair_of_coordinates = np.array(list(product(detected_person, detected_vehicles)), dtype=int)
            if len(pair_of_coordinates) >= 1 :
                for i in range(len(pair_of_coordinates)) :
                    ## 각 조합별 박스 겹침 확인
                    # pair_of_coordinates : (num of combination, 2, 4)
                    # 2 : each person (index 0 or 1)
                    # 4 : x, y, w, h (coordinates)

                    boxOverlapFlag = boxOverlapCheck(pair_of_coordinates[i][0], pair_of_coordinates[i][1])
                    if boxOverlapFlag == 1:
                        if len(self.target) == 15:
                            self.target.pop(0)
                        self.target.append(pair_of_coordinates[i][0])

            if num_of_person >= 2 and num_of_person <= 6 :
                pair_of_center_coordinates = np.array(list(combinations(detected_person, 2)), dtype=int)
                if len(pair_of_center_coordinates) >= 1:
                    for i in range(len(pair_of_center_coordinates)) :
                        boxOverlapFlag = boxOverlapCheck(pair_of_center_coordinates[i][0], pair_of_center_coordinates[i][1])
                        if boxOverlapFlag == 1:
                            if len(self.target) == 15:
                                self.target.pop(0)
                            self.target.append(pair_of_center_coordinates[i][0])                        

        ret = self.opticalFlow(frame['frame'])

        if len(self.history) == 30 :
            self.history.pop(0)
        if ret >= 35:
            self.history.append(1)
        else :
            self.history.append(0)

        if sum(self.history) >= 10:
            self.result = True
        else :
            self.result = False

        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        return self.result