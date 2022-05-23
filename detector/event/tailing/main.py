import os
import cv2
import json
import itertools
import similaritymeasures
from collections import OrderedDict, defaultdict


import time
import numpy as np
import pandas as pd
import math
from itertools import combinations
from scipy.spatial.distance import euclidean

from detector.event.tailing.utils import *
from detector.event.template.main import Event
from detector.tracker.tailing_tracker.BYTETracker import BYTETracker

tracker = BYTETracker(track_thresh=0.5, track_buffer=30, match_thresh=0.8, min_box_area=10, frame_rate=20)

# Notice
# - Dummy class는 참고 및 테스트용이기 때문에 해당 class는 수정 또는 삭제하지 말고 참고만 해주시기 바랍니다.
# - 이미 정의된 함수 및 클래스 멤버 변수의 이름은 *****절대로**** 변경하지마세요.

class TailingEvent(Event):
    model = None
    result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False, tracker_name="byte_tracker"):
        super().__init__(debug)
        self.model_name = "tailing"
        self.analysis_time = 0
        self.debug = debug
        self.history = [0, ] * 40
        self.result = False
        
        self.max_history = 40
        self.frame = None
        self.frame_cnt = 0
        self.row_idx = 0
        self.nonmove_cnt = 0

        self.tracker_name = tracker_name
        self.prev_stack = None
        self.id_dict_stack = {}
        self.id_cp_dict = defaultdict(list)
        self.prev_track_id_list = []
        self.dict = defaultdict(list)
        self.frame_raise = []
        self.smoothBox = []

        # TODO: __init__
        # - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
        # - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
        # - 위의 4개 변수(model_name, analysis_time, debug, result) 중 하나라도 삭제하면 동작이 안되니 유의해주시기 바랍니다.

    def inference(self, frame_info, detection_result, tracking_result, score_threshold=0.5):
        detection_result = self.filter_object_result(detection_result, score_threshold)
        #h,w = frame_info['frame'].shape[0], frame_info['frame'].shape[1]
        start = 0
        end = 0
        self.frame_cnt += 1
        if self.debug:
            start = time.time()

        result = OrderedDict()
        
        boxes_list_array, scores_list_array, classes_list_array = det_to_trk_data_conversion(detection_result)
        tracked_stracks_history = tracker.update(boxes_list_array, scores_list_array, classes_list_array)

        eventFlag = [0, ] * 40
        
        if 2 <= len(tracked_stracks_history):
            human_stracks = [strack for strack in tracked_stracks_history[-1]['tracked_stracks_list'] if strack.cls == 0 and is_not_boundary(strack.xyah) == True and 800 < strack.tlwh[2] * strack.tlwh[3]]
            for human_strack in human_stracks:
                
                track_id = human_strack.track_id
                human_coord = human_strack.xyah[:2]

                if  track_id in self.id_dict_stack:
                    self.id_dict_stack[track_id] += 1
                else:
                    self.id_dict_stack[track_id] = 1
                
                
                if track_id in self.id_cp_dict:
                    self.id_cp_dict[track_id].append(human_coord)
                else:
                    self.id_cp_dict[track_id] = []

                
        if self.frame_cnt >= 40:
            
            temp = []
            temp_dict = {}
            for k, v in self.id_dict_stack.items(): #id, stack count
                if v > 5:  
                    temp.append(k)

            if 4 > len(temp) >= 2:
                equal_id = [t for t in temp if t in self.prev_track_id_list]

                for i in equal_id:
                    coord = np.array(self.id_cp_dict[i])
                    temp_dict[i] = coord
                
                

                coord_values = [v for k, v in temp_dict.items()]
                comb_id = list(combinations(equal_id, 2))

                comb_coords = list(combinations(coord_values, 2))
                dist_compared = np.array(
                    [np.linalg.norm(comb_coords[i][0][-1] - comb_coords[i][1][-1]) for i in range(len(comb_coords))])
                
                combi_frechet = np.array(
                            [similaritymeasures.frechet_dist(comb_coords[i][0], comb_coords[i][1]) for i in
                                range(len(comb_coords))])


                del_idx = []
                for i in range(len(comb_id)):
                    if (dist_compared[i] > 350 or dist_compared[i] < 60) or (dist_compared[i] < combi_frechet[i]):
                        del_idx.append(i)

                
                if del_idx:
                    dist_compared = np.delete(dist_compared, del_idx)
                    combi_frechet = np.delete(combi_frechet, del_idx)
                    
                
                del_person_id = []
                for i in del_idx:
                    del_person_id.append(comb_id[i])
                for i in del_person_id:
                    if i in comb_id:
                        comb_id.remove(i)
                

                if len(combi_frechet) > 0 and len(dist_compared)>0:
                    target_comb = comb_id[np.argmin(combi_frechet)]
                    first_pid = target_comb[0]
                    second_pid = target_comb[1]

                    f_sp, f_ep = temp_dict[first_pid][0], temp_dict[first_pid][-1]
                    s_sp, s_ep = temp_dict[second_pid][0], temp_dict[second_pid][-1]
                    
                    if 0.6 < cos_sim(f_ep, f_sp, s_ep, s_sp) < 1.0:
                        eventFlag = [1, ] * 40
                    else:
                        eventFlag = [0, ] * 40
            else:
                eventFlag = [0, ] * 40

            self.frame_cnt = 0
            self.id_dict_stack = {}
            self.prev_track_id_list = temp
                           

        self.history.extend(eventFlag)
        if len(self.history) >= self.max_history:
            self.history = self.history[40:]
            if sum(self.history) >= 25:
                tmp = 1
            else :
                tmp = 0
        else :
            tmp = 0
        
        
        if len(self.smoothBox) == 200:
            self.smoothBox.pop(0)
        self.smoothBox.append(tmp)                            

        
        if sum(self.smoothBox) >= 2:
            self.result = True
        else :
            self.result = False
        
        
        self.frame = result

        # TODO: analysis(끝 지점)
        if self.debug:
            end = time.time()
            self.analysis_time = end - start

        return self.result