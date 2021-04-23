from collections import OrderedDict

import os
import json
import time
import numpy as np
import math
from itertools import combinations
from detector.event.template.main import Event

# Notice
# - Dummy class는 참고 및 테스트용이기 때문에 해당 class는 수정 또는 삭제하지 말고 참고만 해주시기 바랍니다.
# - 이미 정의된 함수 및 클래스 멤버 변수의 이름은 *****절대로**** 변경하지마세요.

def event_checker(vector_combi):
    eventFlag = 0
    for i in range(vector_combi.shape[0]):
        norm1, norm2 = np.linalg.norm(vector_combi[i][0]), np.linalg.norm(vector_combi[i][1])
        dot = float(np.dot(vector_combi[i][0], vector_combi[i][1]))
        scalar = norm1 * norm2

        if dot==0 and scalar==0:
            dot, scalar = 0.1, 0.1

        elif abs(scalar) < abs(dot):
            if scalar >= 0:
                if dot > 0:
                    scalar = dot
                else:
                    scalar = -dot
            else:
                if dot < 0:
                    scalar = dot
                else:
                    scalar = -dot

        theta = math.acos(dot/scalar)
        deg = (theta*180) / math.pi 

        if deg < 100:
            eventFlag = 1

    return eventFlag

class TailingEvent(Event):
    model = None
    result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False):
        super().__init__(debug)
        self.model_name = "tailing"
        self.analysis_time = 0
        self.debug = debug
        self.history = []
        self.result = 0

        # TODO: __init__
        # - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
        # - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
        # - 위의 4개 변수(model_name, analysis_time, debug, result) 중 하나라도 삭제하면 동작이 안되니 유의해주시기 바랍니다.

        self.max_history = 5
        self.frame = None

    def inference(self, detection_result):
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        result = OrderedDict()
        detected_person = []
        for i, e in enumerate(detection_result['results']):
            if e['label'][0]['description'] in ['person']:
                detected_person.append(
                    ((e['position']['x'] + e['position']['w'] / 2), (e['position']['y'] + e['position']['h'] / 2)))

        num_of_person = len(detected_person)
        result["num_of_person"] = num_of_person
        result["center_coordinates"] = detected_person
        
        # tailing detection module
        combi, tmp_combi = [], []
        eventFlag = 0

        if self.frame != None:

            if num_of_person >= 2 and num_of_person <= 6 and self.frame["num_of_person"] > 0 :

                for i in range(num_of_person):
                    tmp_val = 10000
                    for j in range(self.frame["num_of_person"]):
                        dist = math.sqrt(
                            pow(result["center_coordinates"][i][0] - self.frame["center_coordinates"][j][0], 2) + pow(
                                result["center_coordinates"][i][1] - self.frame["center_coordinates"][j][1], 2))            
                        if dist < tmp_val:
                            tmp_val = dist
                            tmp_combi = (result["center_coordinates"][i], self.frame["center_coordinates"][j])
                    combi.append(tmp_combi)
            
            num_of_combi = len(combi)
            if num_of_combi > 0:
                tmp_vector = []
                for i in range(num_of_combi):
                    now, pre = combi[i][0], combi[i][1]
                    tmp_vector.append((now[0] - pre[0], now[1] - pre[1]))

                vector_combi = np.array(list(combinations(tmp_vector, 2)), dtype=float)
                eventFlag = event_checker(vector_combi)

        if len(self.history) >= self.max_history:
            self.history.pop(0)
        self.history.append(eventFlag)

        # Smoothing (history check)
        sum = 0
        for i in range(len(self.history)):
            if self.history[i] == 1:
                sum += 1

        if sum >= (self.max_history * 0.2):
            state = True
        else:
            state = False

        self.frame = result
        self.result = state

        # TODO: analysis(끝 지점)

        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        return self.result 
