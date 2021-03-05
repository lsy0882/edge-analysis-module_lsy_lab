from collections import OrderedDict

import os
import json
import time

import numpy as np

class Obstacle:
    model = None
    result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug):
        self.model_name = "Obstacle"
        self.analysis_time = 0
        self.debug = debug
        #검출대상(보행장애물)
        self.target = ['bicycle', 'bus', 'car', 'carrier', 'motorcycle', 'movable_signage', 'truck',
                    'bollard', 'chair', 'potted_plant', 'table', 'tree_trunk', 'pole', 'fire_hydrant']           
        self.threshold = 0.5
        self.history = []
        self.max_history = 5

    def analysis_from_json(self, od_result):
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        # result json - image_path, cam_id, frame_num, detected_categories(label, score, center_coordinates)

        received = od_result.decode('utf-8').replace("'", '"') # byte to string
        data = json.loads(received) # load json string

        state = 0
        for _, e in enumerate(data['results'][0]['detection_result']): # json 파일의 검출 객체 목록
            if e['label'][0]['description'] in self.target and e['label'][0]['score'] >= self.threshold : # 객체 목록 중 보행장애물(target)이 있을 경우 리스트에 추가
                state = 1

        if len(self.history) >= self.max_history :
            self.history.pop(0)

        self.history.append(state)

        sum = 0
        if len(self.history) == self.max_history:
            for i in range(self.max_history):
                sum += self.history[i]

        if sum >= (self.max_history * 0.6) :
            state = 1
        else :
            state = 0

        self.result = state

        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        return self.result