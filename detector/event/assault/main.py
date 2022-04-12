import os
import time
from itertools import combinations, product
import numpy as np
import pdb
import math

from detector.event.template.main import Event
from PIL import Image
from .bytetrack.byte_tracker_custom import BYTETracker

# Call BYTE Tracker
tracker = BYTETracker(track_thresh=0.5, track_buffer=30, match_thresh=0.8, min_box_area=10, frame_rate=20)

# Code by LSY
def det_to_trk_data_conversion(detection_result):
    '''
        architecture(detection_result): 
            [
                {'label': [{'description': 'class_name', 'score': float, 'class_idx': int}], 'position': {'x': int, 'y': int, 'w': int, 'h': int}}, ...}
            ]
    '''
    detection_result = detection_result['results'][0]['detection_result']
    boxes_tmp_list = []
    boxes_list = []
    scores_tmp_list = []
    scores_list = []
    classes_tmp_list = []
    classes_list = []
    for info_ in detection_result:
        boxes_tmp_list.append(info_['position']['x'])
        boxes_tmp_list.append(info_['position']['y'])
        boxes_tmp_list.append(info_['position']['x'] + info_['position']['w'])
        boxes_tmp_list.append(info_['position']['y'] + info_['position']['h'])
        scores_tmp_list.append(info_['label'][0]['score'])
        classes_tmp_list.append(info_['label'][0]['class_idx'])
        boxes_list.append(boxes_tmp_list)
        scores_list.append(scores_tmp_list)
        classes_list.append(classes_tmp_list)
        boxes_tmp_list = []
        scores_tmp_list = []
        classes_tmp_list = []
    '''
        arhitecture(boxes_list_array): array([[x0, y0, x1, y1], ... ])
        arhitecture(scores_list_array): array([[score], ... ])
        arhitecture(classes_list_array): array([[class], ... ])
        
        => boxes_list_array, scores_list_array, classes_list_array are detection results that exist in current frame
    '''
    boxes_list_array = np.array(boxes_list)
    scores_list_array = np.array(scores_list)
    classes_list_array = np.array(classes_list)

    return boxes_list_array, scores_list_array, classes_list_array

def is_not_boundary(xyah):
        x = xyah[0]
        y = xyah[1]
        if 20 < x < 605 and 30 < y < 318:
            return True
        else:
            return False


class AssaultEvent(Event):
    model = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False):
        super().__init__(debug)
        self.model_name = "assault"
        self.debug = debug

        self.result = False
        self.frame_count = 0
        self.analysis_time = 0

        self.impact_history = []
        self.merge_history = []
        self.start_assault_true_alarm_frame = 9999999

    def inference(self, frame_info, detection_result, score_threshold=0.1): 
        '''
            architecture(frame_info):
                {
                    'frame': array[ [[], ..., []], ...] => shape: (360, 640, 3),
                    'frame_number': int
                }
            architecture(detection_result):
                {
                    'image_path': 'jpg_path', 'cam_address': 'avi_path', 'module': 'yolov4-416', 'frame_number': int, 'timestamp': '0:00:00:000000',
                    'results': [{'detection result': [{'label': [{'description': 'class_name', 'score': float, 'class_idx': int}], 'position': {'x': int, 'y': int, 'w': int, 'h': int}}, ... ]  }]        
                }
        '''
        detection_result = self.filter_object_result(detection_result, score_threshold)
        frame = frame_info["frame"]
        frame_number = frame_info["frame_number"]
        self.result = False
        self.frame_count += 1
        start = 0
        end = 0

        if self.debug:
            start = time.time()

        boxes_list_array, scores_list_array, classes_list_array = det_to_trk_data_conversion(detection_result)
        tracked_stracks_history = tracker.update(boxes_list_array, scores_list_array, classes_list_array)

        '''
            architecture(tracked_stracks_history):
                [
                    { 
                        'frame_id': frame_id, 'tracked_stracks_list': [current_ids, ...], 'appear_tracked_stracks_list': [appear_ids, ...], 'disap_tracked_stracks_list': [disap_ids, ...],
                        'switch_tracks': [switch_ids, ...], 'separation_stracks': [separation_ids, ...], 'merge_stracks': [merge_ids, ...]'
                    }, ...
                ]
        '''

        # Judge Assaults
        if 2 <= len(tracked_stracks_history):

            ''' Step 1. Initialize variables '''
            human_stracks = [strack for strack in tracked_stracks_history[-1]['tracked_stracks_list'] if strack.cls == 0 and is_not_boundary(strack.xyah) == True and 800 < strack.tlwh[2] * strack.tlwh[3]]
            current_strack_cp = []
            previous_strack_cp = []
            impact_stracks_list = []
            merge_stracks_list = []

            ''' Step 2. Only focus on Overlap situations. '''
            for human_strack in human_stracks:

                ''' Step 3. Obtain "CLOSE" when center point exceeds a threshold that depends on the size of width and height. '''
                if len(human_strack.overlap) != 0:
                    overlaped_human_stracks = human_strack.overlap
                    for overlaped_human_strack in overlaped_human_stracks:
                        close_y_threshold = ((human_strack.tlwh[3] + overlaped_human_strack.tlwh[3]) / 2) / 5.2
                        close_y = abs(human_strack.xyah[1] - overlaped_human_strack.xyah[1])
                        if close_y < close_y_threshold:
                            close_x_threshold = ((human_strack.tlwh[2] + overlaped_human_strack.tlwh[2]) / 2) / 1.26
                            close_x = abs(human_strack.xyah[0] - overlaped_human_strack.xyah[0])
                            if close_x < close_x_threshold:
                                human_strack.action_state = "C" # C is an abbreviation of "CLOSE"

                ''' Step 4. Obtain "IMPACT" state when acceleration exceeds a threshold that depends on the size of the box. '''
                if human_strack.action_state == "C":
                    if 3 <= len(human_strack.cp) and human_strack.cp[-1]['frame_id'] - human_strack.cp[-3]['frame_id'] == 2:
                        pre_previous_cp = human_strack.cp[-3]['center_point']
                        previous_cp = human_strack.cp[-2]['center_point']
                        current_cp = human_strack.cp[-1]['center_point']
                        previous_velocity = np.linalg.norm(previous_cp - pre_previous_cp)
                        current_velocity = np.linalg.norm(current_cp - previous_cp)
                        current_acceleration = np.linalg.norm(current_velocity - previous_velocity)
                        acceleration_threshold = (human_strack.tlwh[2] * human_strack.tlwh[3]) * 0.0005115
                        if acceleration_threshold < current_acceleration < acceleration_threshold * 1.387 and current_acceleration < 5.66 or acceleration_threshold * 3.34 < current_acceleration:
                            human_strack.action_state = "I" # I is an abbreviation of "IMPACT"
                        # exceptive situation (uses weapons ...)
                        if current_velocity < 0.262 and acceleration_threshold / 0.00052 > 4610 and 70 < current_cp[1] < 280:
                            self.start_assault_true_alarm_frame = self.frame_count

                ''' Step 5. Obtain impact & merge strack list to make history. '''
                if human_strack.action_state == "I":
                    impact_stracks_list.append(human_strack)
                if 2 <= human_strack.meta_label:
                    merge_stracks_list.append(human_strack)
            
            ''' Step 6. Record impact & merge history for judging "ASSAULT". '''
            if len(impact_stracks_list) != 0:
                self.impact_history.append({'frame_count': self.frame_count, 'impact_locations': []})
                for impact_strack in impact_stracks_list:
                    self.impact_history[-1]['impact_locations'].append(impact_strack.xyah[:2])

            if len(merge_stracks_list) != 0:
                self.merge_history.append({'frame_count': self.frame_count, 'merge_locations': [], 'merge_box_sizes': []})
                for merge_strack in merge_stracks_list:
                    self.merge_history[-1]['merge_locations'].append(merge_strack.xyah[:2])
                    self.merge_history[-1]['merge_box_sizes'].append(float(merge_strack.tlwh[2] * merge_strack.tlwh[3]))

            ''' Step 7-1. Judge Assault : Preliminary assault signal -> Assault signal '''
            if len(self.impact_history) != 0 and self.impact_history[-1]['frame_count'] == self.frame_count:
                if len(self.impact_history) == 1:
                    self.result = False
                else:
                    current_impact_frame = self.impact_history[-1]['frame_count']
                    previous_impact_frame = self.impact_history[-2]['frame_count']
                    if current_impact_frame - previous_impact_frame <= 40: # fps * 2
                        self.start_assault_true_alarm_frame = self.frame_count
                    else:
                        self.result = False

            ''' Step 7-2. Judge Assault : Preliminary assault signal -> Merge '''
            if len(self.impact_history) != 0 and len(self.merge_history) != 0 and self.merge_history[-1]['frame_count'] == self.frame_count:
                current_merge_frame = self.merge_history[-1]['frame_count']
                current_merge_locations = self.merge_history[-1]['merge_locations']
                current_merge_box_sizes = self.merge_history[-1]['merge_box_sizes']
                recent_impact_frame = self.impact_history[-1]['frame_count']
                recent_impact_locations = self.impact_history[-1]['impact_locations']
                for current_merge_location_idx in range(len(current_merge_locations)):
                    for recent_impact_location in recent_impact_locations:
                        distance = np.linalg.norm(current_merge_locations[current_merge_location_idx] - recent_impact_location)
                        distance_threshold = current_merge_box_sizes[current_merge_location_idx] * 0.003
                        if current_merge_frame - recent_impact_frame <= 40 and distance <= distance_threshold:
                            self.start_assault_true_alarm_frame = self.frame_count
                        else:
                            self.result = False

            ''' Step 8. A True alarm occurs for 40 frames from the attack signal. ''' # fps * 2
            if 0 <= self.frame_count - self.start_assault_true_alarm_frame <= 40:
                self.result = True

    
        if self.debug:
            end = time.time()
            self.analysis_time = end - start

        return self.result

    # Thx you falldown and wanderer
    def merge_sequence(self, frame_info, end_flag):
        self.frameseq = super().merge_sequence(frame_info,end_flag)
        assault_frame_seq = self.frameseq
        if len(assault_frame_seq) >= 2:
            back_start = assault_frame_seq[-1]['start_frame']
            back_end = assault_frame_seq[-1]['end_frame']
            front_start = assault_frame_seq[-2]['start_frame']
            front_end = assault_frame_seq[-2]['end_frame']
            gap = back_start - front_end
            if gap <= 40:
                del assault_frame_seq[-2:]
                merged_seq = {}
                merged_seq['start_frame'] = front_start
                merged_seq['end_frame'] = back_end
                assault_frame_seq.append(merged_seq)
            else: 
                pass
        self.frameseq = assault_frame_seq
        
        return self.frameseq