import os
import time
import numpy as np

from detector.event.template.main import Event
from detector.tracker.byte_tracker.BYTETracker import BYTETracker

class AssaultEvent(Event):
    model = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False, tracker_name="byte_tracker"):
        super().__init__(debug)
        self.model_name = "assault"
        self.debug = debug

        self.result = False
        self.frame_count = 0
        self.analysis_time = 0

        self.tracked_stracks_history = []
        self.impact_history = []
        self.merge_history = []
        self.start_assault_true_alarm_frame = 9999999
        self.tracker_name = tracker_name

    def inference(self, frame_info, detection_result, tracking_result, score_threshold=0.1):
        frame = frame_info["frame"]
        frame_number = frame_info["frame_number"]

        start = 0
        end = 0

        if self.debug:
            start = time.time()

        # TODO: analysis(시작 지점)
        self.result = False
        self.frame_count += 1

        tracked_stracks = tracking_result
        self.tracked_stracks_history.append({'frame_id': self.frame_count, 'tracked_stracks_list': tracked_stracks, 'appear_tracked_stracks_list': [],
                                            'disap_tracked_stracks_list': [], 'switch_stracks': [], 'separation_stracks': [], 'merge_stracks': []})

        if 2 <= self.frame_count:
            appear_tracked_stracks_list = list(set(tracked_stracks) - set(self.tracked_stracks_history[-2]['tracked_stracks_list']))
            appear_tracked_stracks_list = [
                appear_tracked_strack for appear_tracked_strack in appear_tracked_stracks_list 
                if (is_not_boundary1(appear_tracked_strack.xyah) == True)
                ]
            self.tracked_stracks_history[-1]['appear_tracked_stracks_list'] = appear_tracked_stracks_list

            disap_tracked_stracks_list = list(set(self.tracked_stracks_history[-2]['tracked_stracks_list']) - set(tracked_stracks))
            disap_tracked_stracks_list = [
                disap_tracked_strack for disap_tracked_strack in disap_tracked_stracks_list 
                if (is_not_boundary1(disap_tracked_strack.xyah) == True)
                ]
            self.tracked_stracks_history[-1]['disap_tracked_stracks_list'] = disap_tracked_stracks_list
            
            for appear_tracked_strack in self.tracked_stracks_history[-1]['appear_tracked_stracks_list']:
                appear_tracked_strack_cp = (appear_tracked_strack.xyah[0], appear_tracked_strack.xyah[1])

                if 1 <= len(self.tracked_stracks_history[-1]['disap_tracked_stracks_list']):
                    appear_vs_disap_disatances_list = []
                    for disap_tracked_strack in self.tracked_stracks_history[-1]['disap_tracked_stracks_list']:
                        disap_tracked_strack_cp = (disap_tracked_strack.xyah[0], disap_tracked_strack.xyah[1])
                        appear_vs_disap_distance = np.sqrt((appear_tracked_strack_cp[0] - disap_tracked_strack_cp[0])**2
                                                            + (appear_tracked_strack_cp[1] - disap_tracked_strack_cp[1])**2)
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
                        tracked_strack_except_appear_strack_cp = (tracked_strack_except_appear_strack.xyah[0], tracked_strack_except_appear_strack.xyah[1])
                        appear_vs_total_distance = np.sqrt((appear_tracked_strack_cp[0] - tracked_strack_except_appear_strack_cp[0])**2
                                                            + (appear_tracked_strack_cp[1] - tracked_strack_except_appear_strack_cp[1])**2)
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
                disap_tracked_strack_cp = (disap_tracked_strack.xyah[0], disap_tracked_strack.xyah[1])
                if disap_tracked_strack.switch_state == False:
                    disap_vs_total_distances_list = []
                    for tracked_strack in self.tracked_stracks_history[-1]['tracked_stracks_list']:
                        tracked_strack_cp = (tracked_strack.xyah[0], tracked_strack.xyah[1])
                        disap_vs_total_distance = np.sqrt((disap_tracked_strack_cp[0] - tracked_strack_cp[0])**2 
                                                            + (disap_tracked_strack_cp[1] - tracked_strack_cp[1])**2)
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


        if 2 <= len(self.tracked_stracks_history):

            human_stracks = [strack for strack in self.tracked_stracks_history[-1]['tracked_stracks_list'] if is_not_boundary2(strack.xyah) == True and 800 < strack.tlwh[2] * strack.tlwh[3]]
            current_strack_cp = []
            previous_strack_cp = []
            impact_stracks_list = []
            merge_stracks_list = []

            for human_strack in human_stracks:
                if len(human_strack.overlap) != 0:
                    overlaped_human_stracks = human_strack.overlap
                    for overlaped_human_strack in overlaped_human_stracks:
                        close_y_threshold = ((human_strack.tlwh[3] + overlaped_human_strack.tlwh[3]) / 2) / 5.2
                        close_y = abs(human_strack.xyah[1] - overlaped_human_strack.xyah[1])
                        if close_y < close_y_threshold:
                            close_x_threshold = ((human_strack.tlwh[2] + overlaped_human_strack.tlwh[2]) / 2) / 1.26
                            close_x = abs(human_strack.xyah[0] - overlaped_human_strack.xyah[0])
                            if close_x < close_x_threshold:
                                human_strack.action_state = "C"
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
                            human_strack.action_state = "I"
                        if current_velocity < 0.262 and acceleration_threshold / 0.00052 > 4610 and 70 < current_cp[1] < 280:
                            self.start_assault_true_alarm_frame = self.frame_count
                if human_strack.action_state == "I":
                    impact_stracks_list.append(human_strack)
                if 2 <= human_strack.meta_label:
                    merge_stracks_list.append(human_strack)
            
            if len(impact_stracks_list) != 0:
                self.impact_history.append({'frame_count': self.frame_count, 'impact_locations': []})
                for impact_strack in impact_stracks_list:
                    self.impact_history[-1]['impact_locations'].append(impact_strack.xyah[:2])

            if len(merge_stracks_list) != 0:
                self.merge_history.append({'frame_count': self.frame_count, 'merge_locations': [], 'merge_box_sizes': []})
                for merge_strack in merge_stracks_list:
                    self.merge_history[-1]['merge_locations'].append(merge_strack.xyah[:2])
                    self.merge_history[-1]['merge_box_sizes'].append(float(merge_strack.tlwh[2] * merge_strack.tlwh[3]))

            if len(self.impact_history) != 0 and self.impact_history[-1]['frame_count'] == self.frame_count:
                if len(self.impact_history) == 1:
                    self.result = False
                else:
                    current_impact_frame = self.impact_history[-1]['frame_count']
                    previous_impact_frame = self.impact_history[-2]['frame_count']
                    if current_impact_frame - previous_impact_frame <= 40:
                        self.start_assault_true_alarm_frame = self.frame_count
                    else:
                        self.result = False

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

            if 0 <= self.frame_count - self.start_assault_true_alarm_frame <= 120:
                self.result = True

        if self.debug:
            end = time.time()
            self.analysis_time = end - start

        return self.result

    def merge_sequence(self, frame_info, end_flag):
        self.frameseq = super().merge_sequence(frame_info,end_flag)
        assault_frame_seq = self.frameseq
        if len(assault_frame_seq) >= 2:
            back_start = assault_frame_seq[-1]['start_frame']
            back_end = assault_frame_seq[-1]['end_frame']
            front_start = assault_frame_seq[-2]['start_frame']
            front_end = assault_frame_seq[-2]['end_frame']
            gap = back_start - front_end
            if gap <= 120:
                del assault_frame_seq[-2:]
                merged_seq = {}
                merged_seq['start_frame'] = front_start
                merged_seq['end_frame'] = back_end
                assault_frame_seq.append(merged_seq)
            else: 
                pass
        self.frameseq = assault_frame_seq
        
        return self.frameseq

def is_not_boundary1(xyah):
    x = xyah[0]
    y = xyah[1]
    if 20 < x < 620 and 30 < y < 330:
        return True
    else:
        return False

def is_not_boundary2(xyah):
    x = xyah[0]
    y = xyah[1]
    if 20 < x < 605 and 30 < y < 318:
        return True
    else:
        return False