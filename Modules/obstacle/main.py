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
        self.threshold = 0.7
        self.history = []
        self.history_state = []
        self.max_history = 10

    def analysis_from_json(self, od_result):
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        # result json - image_path, cam_id, frame_num, detected_categories(label, score, center_coordinates)

        received = od_result.decode('utf-8').replace("'", '"') # byte to string
        data = json.loads(received) # load json string

        result = OrderedDict()
        detected_categories = [] # 검출된 보행 장애물 목록을 담을 리스트

        result["frame_num"] = data["frame_num"]

        for _, e in enumerate(data['results'][0]['detection_result']): # json 파일의 검출 객체 목록
            if e['label'][0]['description'] in self.target and e['label'][0]['score'] >= self.threshold : # 객체 목록 중 보행장애물(target)이 있을 경우 리스트에 추가
                obstacles = OrderedDict()
                obstacles["label"] = e['label'][0]['description'] 
                obstacles["center_coordinates"] = ( (e['position']['x'] + e['position']['w'])/2, (e['position']['y'] + e['position']['h'])/2 ) # 객체 위치의 중앙값
                obstacles["position"] = e['position']
                detected_categories.append(obstacles)

        result["detected_obstacle"] = detected_categories

        if len(self.history) >= self.max_history :
            self.history.pop(0)

        self.history.append(result)

        check = 0
        current = self.history[-1]["detected_obstacle"]
        previous = self.history[-2]["detected_obstacle"]

        for i in range(len(current)) : 
            for j in range(len(previous)) :
                current_split = current[i]
                previous_split = previous[j]
                if current_split["label"] == previous_split["label"] :
                    dist = np.linalg.norm(np.array(current_split["center_coordinates"]) - np.array(previous_split["center_coordinates"]))
                    if dist <= 10 :
                        check = 1

        if len(self.history_state) >= self.max_history :
            self.history_state.pop(0)

        if check == 1 :
            self.history_state.append(1)
        else :
            self.history_state.append(0)

        check = 0
        for i in range(len(self.history_state)) :
            if self.history_state[i] == 1 :
                check += 1

        prob = check / len(self.history_state)
        if prob > 0.8 :
            state = 1
        else :
            state = 0

        self.result = state

        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        return self.result