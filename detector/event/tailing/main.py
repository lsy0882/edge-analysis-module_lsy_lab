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

        # TODO: analysis(시작 지점)
        # - 분석에 필요한 내용을 작성해주실 부분입니다.
        # - 마지막 라인(return self.result)는 테스트 코드에서 확인하기 위한 코드이며 실제로는 thread에서 사용하지 않습니다.
        #   따라서 반드시 결과 값은 self.result에 저장하시기 바라며, 마지막 라인은 변경하지 마시기 바랍니다.
        # - 이전 프레임의 결과를 사용해야하는 모듈들의 경우 self.history에 저장한 후 사용하시기 바랍니다.
        # - self.result에는 True 또는 False 값으로 이벤트 검출 결과를 저장해주시기 바랍니다.

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
        if num_of_person >= 2 and num_of_person <= 8:
            pair_of_center_coordinates = np.array(list(combinations(detected_person, 2)), dtype=int)
            if len(pair_of_center_coordinates) >= 1:
                for i in range(len(pair_of_center_coordinates)):
                    dist = np.linalg.norm(pair_of_center_coordinates[i][0] - pair_of_center_coordinates[i][1])
                    if dist < 60:
                        eventFlag = 1

        # tailing detection module
        vector = OrderedDict()
        mapping, tmp_combi = [], []
        if self.frame != None:
            if num_of_person >= 2 and num_of_person <= 8 and self.frame["num_of_person"] > 0:
                for i in range(num_of_person):  # 현재 검출 정보
                    tmp_val = 10000
                    for j in range(self.frame["num_of_person"]):  # 이전 프레임 검출 정보
                        dist = math.sqrt(
                            pow(result["center_coordinates"][i][0] - self.frame["center_coordinates"][j][0], 2) + pow(
                                result["center_coordinates"][i][1] - self.frame["center_coordinates"][j][1], 2))
                        if dist < tmp_val:
                            tmp_val = dist
                            tmp_combi = (result["center_coordinates"][i], self.frame["center_coordinates"][j])
                    mapping.append(tmp_combi)

        vector["num_of_mapping"] = len(mapping)
        vector["mapped_coordinates"] = mapping

        self.frame = result

        if vector["num_of_mapping"] > 0:
            tmp_vector = []
            for i in range(vector["num_of_mapping"]):
                first, last = vector["mapped_coordinates"][i][1], vector["mapped_coordinates"][i][0]
                tmp_vector.append((last[0] - first[0], last[1] - first[1]))

            vector["vector"] = tmp_vector
            vector_combi = np.array(list(combinations(vector["vector"], 2)), dtype=float)

            for i in range(vector_combi.shape[0]):
                norm1, norm2 = np.linalg.norm(vector_combi[i][0]), np.linalg.norm(vector_combi[i][1])
                theta = math.acos(float(np.dot(vector_combi[i][0], vector_combi[i][1]) / (norm1 * norm2)))
                deg = (theta * 180) / math.pi
                if deg < 100:
                    eventFlag = 1

        if len(self.history) >= self.max_history:
            self.history.pop(0)
        self.history.append(eventFlag)

        # Smoothing (history check)
        sum = 0
        if len(self.history) == self.max_history:
            for i in range(self.max_history):
                if self.history[i] == 1:
                    sum += 1

        if sum >= (self.max_history * 0.4):
            state = 1
        else:
            state = 0

        self.result = state

        # TODO: analysis(끝 지점)

        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        return self.result