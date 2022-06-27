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
from detector.tracker.byte_tracker.BYTETracker import BYTETracker

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
        self.tracked_stracks_history = []
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

    def inference(self, frame_info, detection_result, tracking_result, score_threshold=0.3):
        detection_result = self.filter_object_result(detection_result, score_threshold)
        ry, rx = 167, 42
        start = 0
        end = 0
        self.frame_cnt += 1
        if self.debug:
            start = time.time()

        result = OrderedDict()
        
        tracked_stracks = tracking_result[:-1]

        self.tracked_stracks_history.append({'frame_count': self.frame_cnt, 'tracked_stracks_list': tracked_stracks, 'appear_tracked_stracks_list': [],
                                            'disap_tracked_stracks_list': [], 'switch_stracks': [], 'separation_stracks': [], 'merge_stracks': []})

        if 2 <= self.frame_cnt:
            appear_tracked_stracks_list = list(set(self.tracked_stracks_history[-1]['tracked_stracks_list']) - set(self.tracked_stracks_history[-2]['tracked_stracks_list']))
            appear_tracked_stracks_list = [appear_tracked_strack for appear_tracked_strack in appear_tracked_stracks_list if (is_not_boundary(appear_tracked_strack.xyah) == True)]
            self.tracked_stracks_history[-1]['appear_tracked_stracks_list'] = appear_tracked_stracks_list

            disap_tracked_stracks_list = list(set(self.tracked_stracks_history[-2]['tracked_stracks_list']) - set(self.tracked_stracks_history[-1]['tracked_stracks_list']))
            disap_tracked_stracks_list = [disap_tracked_strack for disap_tracked_strack in disap_tracked_stracks_list if (is_not_boundary(disap_tracked_strack.xyah) == True)]
            self.tracked_stracks_history[-1]['disap_tracked_stracks_list'] = disap_tracked_stracks_list
            
            for appear_tracked_strack in self.tracked_stracks_history[-1]['appear_tracked_stracks_list']:
                appear_tracked_strack_cp = np.asarray([appear_tracked_strack.xyah[0], appear_tracked_strack.xyah[1]])

                if 1 <= len(self.tracked_stracks_history[-1]['disap_tracked_stracks_list']):
                    appear_vs_disap_disatances_list = []
                    for disap_tracked_strack in self.tracked_stracks_history[-1]['disap_tracked_stracks_list']:
                        disap_tracked_strack_cp = np.asarray([disap_tracked_strack.xyah[0], disap_tracked_strack.xyah[1]])
                        appear_vs_disap_distance = np.linalg.norm(appear_tracked_strack_cp - disap_tracked_strack_cp)
                        appear_vs_disap_disatances_list.append(appear_vs_disap_distance)

                    if len(appear_vs_disap_disatances_list) != 0:
                        appear_vs_disap_min_distance = min(appear_vs_disap_disatances_list)
                        appear_vs_disap_min_distance_idx = appear_vs_disap_disatances_list.index(appear_vs_disap_min_distance)
                        if appear_vs_disap_min_distance < 100 * (appear_tracked_strack_cp[1] / 360)**2:
                            id_switched_strack = self.tracked_stracks_history[-1]['disap_tracked_stracks_list'][appear_vs_disap_min_distance_idx]
                            self.tracked_stracks_history[-1]['switch_stracks'].append(id_switched_strack)
                            appear_tracked_strack.meta_label = id_switched_strack.meta_label
                            appear_tracked_strack.switch_state = True
                            id_switched_strack.meta_label = 1
                            id_switched_strack.switch_state = True

                if appear_tracked_strack.switch_state == False:
                    appear_vs_total_distances_list = []
                    tracked_stracks_list_except_appear_strack = [
                        tracked_strack for tracked_strack in self.tracked_stracks_history[-1]['tracked_stracks_list'] 
                        if tracked_strack is not appear_tracked_strack
                        ]
                    merge_strack = None
                    for tracked_strack_except_appear_strack in tracked_stracks_list_except_appear_strack:
                        if appear_tracked_strack in tracked_strack_except_appear_strack.merge:
                            merge_strack = tracked_strack_except_appear_strack
                            merge_strack.merge.remove(appear_tracked_strack)
                        tracked_strack_except_appear_strack_cp = np.asarray([tracked_strack_except_appear_strack.xyah[0], tracked_strack_except_appear_strack.xyah[1]])
                        appear_vs_total_distance = np.linalg.norm(appear_tracked_strack_cp - tracked_strack_except_appear_strack_cp)
                        appear_vs_total_distances_list.append(appear_vs_total_distance)
                    if len(appear_vs_total_distances_list) != 0:
                        appear_vs_total_min_distance = min(appear_vs_total_distances_list)
                        appear_vs_total_min_distance_idx = appear_vs_total_distances_list.index(appear_vs_total_min_distance)

                    if merge_strack is not None:
                        self.tracked_stracks_history[-1]['separation_stracks'].append(merge_strack)
                        merge_strack.meta_label -= 1
                    elif merge_strack is None and len(appear_vs_total_distances_list) != 0:
                        if appear_vs_total_min_distance < 200 * (appear_tracked_strack_cp[1] / 360)**2:
                            separated_strack = tracked_stracks_list_except_appear_strack[appear_vs_total_min_distance_idx]
                            if 2 <= separated_strack.meta_label:
                                self.tracked_stracks_history[-1]['separation_stracks'].append(separated_strack)
                                separated_strack.meta_label -= 1
            
            for disap_tracked_strack in self.tracked_stracks_history[-1]['disap_tracked_stracks_list']:
                disap_tracked_strack_cp = np.asarray([disap_tracked_strack.xyah[0], disap_tracked_strack.xyah[1]])
                if disap_tracked_strack.switch_state == False:
                    disap_vs_total_distances_list = []
                    for tracked_strack in self.tracked_stracks_history[-1]['tracked_stracks_list']:
                        tracked_strack_cp = np.asarray([tracked_strack.xyah[0], tracked_strack.xyah[1]])
                        disap_vs_total_distance = np.linalg.norm(disap_tracked_strack_cp - tracked_strack_cp)
                        disap_vs_total_distances_list.append(disap_vs_total_distance)
                    if len(disap_vs_total_distances_list) != 0:
                        disap_vs_total_min_distance = min(disap_vs_total_distances_list)
                        disap_vs_total_min_distance_idx = disap_vs_total_distances_list.index(disap_vs_total_min_distance)
                        if disap_vs_total_min_distance < 200 * (disap_tracked_strack_cp[1] / 360)**2:
                            merged_strack = self.tracked_stracks_history[-1]['tracked_stracks_list'][disap_vs_total_min_distance_idx]
                            if (1 / merged_strack.xyah[2]) < 2.7:
                                self.tracked_stracks_history[-1]['merge_stracks'].append(merged_strack)
                                merged_strack.merge.append(disap_tracked_strack)
                                merged_strack.merge = list(set(merged_strack.merge))
                                merged_strack.meta_label += disap_tracked_strack.meta_label
                    disap_tracked_strack.meta_label = 1


        
        eventFlag = [0, ] * 40
        
        if 2 <= len(self.tracked_stracks_history):
            human_stracks = [strack for strack in self.tracked_stracks_history[-1]['tracked_stracks_list'] if strack.cls == 0 and is_not_boundary(strack.xyah) == True and 800 < strack.tlwh[2] * strack.tlwh[3]]
            for human_strack in human_stracks:
                
                track_id = human_strack.track_id
                #human_coord = human_strack.xyah[:2]
                human_coord = human_strack.xyah

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
                if v > 10:  
                    temp.append(k)

            if 4 > len(temp) >= 2:
                equal_id = [t for t in temp if t in self.prev_track_id_list]

                for i in equal_id:
                    coord = np.array(self.id_cp_dict[i])
                    temp_dict[i] = coord
                
                

                coord_values = [v for k, v in temp_dict.items()]
                comb_id = list(combinations(equal_id, 2))

                comb_coords = list(combinations(coord_values, 2))
                
                

                relative_dist_list=[]
                for i in range(len(comb_coords)):
                    a1, h1 = comb_coords[i][0][-1, 2:]
                    w1 = a1 * h1
                    a2, h2 = comb_coords[i][1][-1, 2:]
                    w2 = a2 * h2

                    rd_a = np.sqrt((w1*h1) / (rx * ry))
                    rd_b = np.sqrt((w2*h2) / (rx * ry))
                    relative_dist = np.abs((rd_a - rd_b)/rd_a)
                    relative_dist_list.append(relative_dist)
                    
                combi_frechet = np.array(
                            [similaritymeasures.frechet_dist(comb_coords[i][0][::2], comb_coords[i][1][::2]) for i in
                                range(len(comb_coords))])


                del_idx = []
                for i in range(len(comb_id)):
                    if (relative_dist_list[i] > 0.8 or relative_dist_list[i] < 0.2):
                        del_idx.append(i)

                
                if del_idx:
                    relative_dist_list = np.delete(relative_dist_list, del_idx)
                    combi_frechet = np.delete(combi_frechet, del_idx)
                    
                
                del_person_id = []
                for i in del_idx:
                    del_person_id.append(comb_id[i])
                for i in del_person_id:
                    if i in comb_id:
                        comb_id.remove(i)
                
                
                if len(combi_frechet) > 0 and len(relative_dist_list)>0:
                    target_comb = comb_id[np.argmin(combi_frechet)]
                    first_pid = target_comb[0]
                    second_pid = target_comb[1]

                    f_sp, f_ep = temp_dict[first_pid][0], temp_dict[first_pid][-1]
                    s_sp, s_ep = temp_dict[second_pid][0], temp_dict[second_pid][-1]
                    if 0.5 < cos_sim(f_ep, f_sp, s_ep, s_sp) < 1.0:
                        eventFlag = [1, ] * 40
                    else:
                        eventFlag = [0, ] * 40
            else:
                eventFlag = [0, ] * 40

            self.frame_cnt = 0
            self.id_dict_stack = {}
            self.id_cp_dict = defaultdict(list)
            self.prev_track_id_list = temp

            del temp, temp_dict
                           

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