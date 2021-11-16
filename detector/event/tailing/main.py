from collections import OrderedDict

import os
import cv2
import json
import itertools
import similaritymeasures
import time
import numpy as np
import math
from itertools import combinations
from detector.event.template.main import Event


# Notice
# - Dummy class는 참고 및 테스트용이기 때문에 해당 class는 수정 또는 삭제하지 말고 참고만 해주시기 바랍니다.
# - 이미 정의된 함수 및 클래스 멤버 변수의 이름은 *****절대로**** 변경하지마세요.
def cos_sim(v1_1, v1_2, v2_1, v2_2):
    vector_1 = v1_2 - v1_1
    vector_2 = v2_2 - v2_1
    if vector_1[0] == 0.0:
        vector_1[0] = 0.01

    if vector_1[1] == 0.0:
        vector_1[1] = 0.01

    if vector_2[0] == 0.0:
        vector_2[0] = 0.01

    if vector_2[1] == 0.0:
        vector_2[1] = 0.01

    return np.dot(vector_1, vector_2) / (np.linalg.norm(vector_1) * np.linalg.norm(vector_2))

def check_zeroValue(coordinates, n):
    if coordinates[n][0] == 0.0 or coordinates[n][1] == 0.0:
        return check_zeroValue(coordinates, n - 1)
    else:
        return coordinates[n]


class TailingEvent(Event):
    model = None
    result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False):
        super().__init__(debug)
        self.model_name = "tailing"
        self.analysis_time = 0
        self.debug = debug
        self.history = [0, ] * 5
        self.result = False

        self.frechet_dl = np.zeros(shape=(6,6, 2), dtype=np.float32)
        self.max_history = 50
        self.frame = None
        self.frame_cnt = 0
        self.row_idx = 0

        self.mask = None
        self.prev_mask = None
        self.prev_frame = None
        self.nonmove_cnt = 0

        self.smoothBox = []

        # TODO: __init__
        # - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
        # - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
        # - 위의 4개 변수(model_name, analysis_time, debug, result) 중 하나라도 삭제하면 동작이 안되니 유의해주시기 바랍니다.

    def inference(self, frame, detection_result):
        start = 0
        end = 0
        if self.debug:
            start = time.time()

        result = OrderedDict()
        detected_person = []
        person_bbox = []
        for i, e in enumerate(detection_result['results'][0]["detection_result"]):
            if e['label'][0]['description'] in ['person'] and e['label'][0]['score'] >= 0.60 and e['position']['x'] + (e['position']['w'] < e['position']['y'] + e['position']['h']):
                detected_person.append(
                    ((e['position']['x'] + e['position']['w'] / 2), (e['position']['y'] + e['position']['h'] / 2)))
                person_bbox.append([e['position']['x'], e['position']['y'], e['position']['w'], e['position']['h']])

        num_of_person = len(detected_person)
        result["num_of_person"] = num_of_person
        result["center_coordinates"] = detected_person

        # tailing detection module
        # 시작 5frame은 0인 상태
        eventFlag = [0, ] * 5
        tmp = 0
        result["center_coordinates"] = sorted(result["center_coordinates"])
        
        if self.frame != None:
            if result["num_of_person"] != 2 and self.frame["num_of_person"] != 2:
                self.frechet_dl = np.zeros(shape=(11, 11, 2), dtype=np.float32)
                self.max_history = 5
                self.frame = None
                self.result = False
                self.frame_cnt = 0
                self.nonmove_cnt = 0
                self.row_idx = 0
                eventFlag = [0, ] * 5

            elif result["num_of_person"] >= 2:
                self.frechet_dl[self.row_idx, :len(result["center_coordinates"])] = result["center_coordinates"]
                if self.row_idx >= 5:
                    self.row_idx = 0
                else:
                    self.row_idx += 1

                if self.frame_cnt >= 5:
                    each_person_cordinates = []  # 검출된 사람마다의 각 이동좌표를 하나의 열로 연결
                    combi_frechet = []

                    r_list, c_list = [], []
                    for i in range(len(self.frechet_dl)):
                        if np.sum(self.frechet_dl[i]) == 0.0:
                            r_list.append(i)
                        if np.sum(self.frechet_dl[:, i]) == 0.0:
                            c_list.append(i)

                    self.frechet_dl = np.delete(self.frechet_dl, r_list, axis=0)
                    self.frechet_dl = np.delete(self.frechet_dl, c_list, axis=1)

                    
                    
                    index_cnt = 0
                    ln = int(self.frechet_dl.shape[0]) - 1
                    for i in range(self.frechet_dl.shape[1]):
                        last_point = check_zeroValue(self.frechet_dl[:, index_cnt], ln)
                        point_movement = last_point - self.frechet_dl[:, index_cnt][0]
                        if abs(point_movement[0]) < 1.5 and abs(point_movement[1]) < 1.5:
                            
                            self.frechet_dl = np.delete(self.frechet_dl, index_cnt, axis=1)
                            index_cnt = 0
                        else:
                            index_cnt += 1

                    
                    if 3 > self.frechet_dl.shape[1] >= 2:
                        transpose_frechet_dl = list(map(list, zip(*self.frechet_dl)))
                        each_person_comb = np.array(list(combinations(transpose_frechet_dl, 2)), dtype=float)
                        combi_frechet = np.array(
                            [similaritymeasures.frechet_dist(each_person_comb[i][0], each_person_comb[i][1]) for i in
                             range(len(each_person_comb))])
                        
                        if (combi_frechet.size == 0) is False:
                            min_idx = np.argmin(combi_frechet)

                            # 각 사람 start point, end point
                            ln = len(each_person_comb[min_idx][0]) - 1
                            p1_sp, p1_ep = each_person_comb[min_idx][0][0], check_zeroValue(
                                each_person_comb[min_idx][0], ln)
                            p2_sp, p2_ep = each_person_comb[min_idx][1][0], check_zeroValue(
                                each_person_comb[min_idx][1], ln)

    
                            dist = np.linalg.norm(p1_ep - p2_ep)
                            
                            movement = abs(np.linalg.norm(p1_ep - p1_sp) - np.linalg.norm(p2_ep - p2_sp))
                            compare_simiarity = abs(combi_frechet[0] - dist)
                            

                            if 1.0 >= cos_sim(p1_sp, p1_ep, p2_sp, p2_ep) > 0.0 and dist > 100.0 and movement < 40.0 and compare_simiarity < 20.0:
                                eventFlag = [1, ] * 5
                            else:
                                eventFlag = [0, ] * 5

                    else:
                        eventFlag = [0, ] * 5

                    self.frechet_dl = np.zeros(shape=(6, 6, 2), dtype=np.float32)
                    self.frame_cnt = 0
                    
                    self.history.extend(eventFlag)
                    if len(self.history) >= self.max_history:
                        self.history = self.history[5:]
                        if sum(self.history) >= 3:
                            tmp = 1
                        else :
                            tmp = 0
                    else :
                        tmp = 0
        else :
            tmp = 0

        if len(self.smoothBox) == 300:
            self.smoothBox.pop(0)
        self.smoothBox.append(tmp)                            

        if sum(self.smoothBox) >= 5:
            self.result = True
        else :
            self.result = False
        
        self.frame_cnt += 1
        self.frame = result

        # TODO: analysis(끝 지점)
        if self.debug:
            end = time.time()
            self.analysis_time = end - start

        return self.result



