import numpy as np
from collections import deque
import os
import os.path as osp
import copy
import torch
import torch.nn.functional as F

from itertools import combinations

from .kalman_filter import KalmanFilter
from . import matching
from .basetrack import BaseTrack, TrackState

import pdb


class STrack(BaseTrack):
    shared_kalman = KalmanFilter()
    def __init__(self, tlwh, score, cls):
        ''' wait activate. In this step, STrack is just detection box'''
        # wait activate
        self._tlwh = np.asarray(tlwh, dtype=np.float)
        self.score = score
        self.cls=cls
        self.kalman_filter = None
        self.mean, self.covariance = None, None
        self.is_activated = False
        self.tracklet_len = 0
        self.cp = []
        self.overlap = [] # Code by LSY
        self.merge = [] # Code by LSY
        self.meta_label = 1 # Code by LSY
        self.switch_state = False # Code by LSY
        self.action_state = None # Code by LSY

    def record_center_point(frame, stracks):
        for strack in stracks:
            center_point = np.asarray([strack.xyah[0], strack.xyah[1]])
            strack.cp.append({'frame_id': frame, 'center_point': center_point})
    
    def check_overlap(stracks):
        if len(stracks) > 0:
            combination_stracks = list(combinations(stracks, 2))
            for a_strack, b_strack in combination_stracks:
                if a_strack.cls == 0 and b_strack.cls == 0:
                    if (
                            ((b_strack.tlbr[0] <= a_strack.tlbr[0] <= b_strack.tlbr[2] or b_strack.tlbr[0] <= a_strack.tlbr[2] <= b_strack.tlbr[2]) and (b_strack.tlbr[1] <= a_strack.tlbr[1] <= b_strack.tlbr[3] or b_strack.tlbr[1] <= a_strack.tlbr[3] <= b_strack.tlbr[3])) or 
                            ((a_strack.tlbr[0] <= b_strack.tlbr[0] <= a_strack.tlbr[2] or a_strack.tlbr[0] <= b_strack.tlbr[2] <= a_strack.tlbr[2]) and (a_strack.tlbr[1] <= b_strack.tlbr[1] <= a_strack.tlbr[3] or a_strack.tlbr[1] <= b_strack.tlbr[3] <= a_strack.tlbr[3]))
                        ):
                        a_strack.overlap.append(b_strack)
                        set(a_strack.overlap)
                        b_strack.overlap.append(a_strack)
                        set(b_strack.overlap)

    def init_switch_action_state(stracks):
        for strack in stracks:
            strack.switch_state = False
            strack.action_state = None

    def init_overlap(stracks):
        for strack in stracks:
            strack.overlap = []

    def predict(self):
        mean_state = self.mean.copy()
        if self.state != TrackState.Tracked:
            mean_state[7] = 0
        self.mean, self.covariance = self.kalman_filter.predict(
            mean_state, self.covariance)

    @staticmethod
    def multi_predict(stracks):
        if len(stracks) > 0:
            multi_mean = np.asarray([st.mean.copy() for st in stracks])
            multi_covariance = np.asarray([st.covariance for st in stracks])
            for i, st in enumerate(stracks):
                if st.state != TrackState.Tracked:
                    multi_mean[i][7] = 0
            multi_mean, multi_covariance = STrack.shared_kalman.multi_predict(multi_mean, multi_covariance)
            for i, (mean, cov) in enumerate(zip(multi_mean, multi_covariance)):
                stracks[i].mean = mean
                stracks[i].covariance = cov

    def activate(self, kalman_filter, frame_id):
        """Start a new tracklet"""
        self.kalman_filter = kalman_filter
        self.track_id = self.next_id()
        self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xyah(self._tlwh))

        self.tracklet_len = 0
        self.state = TrackState.Tracked
        if frame_id == 1:
            self.is_activated = True
        # self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id

    def re_activate(self, new_track, frame_id, new_id=False):
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyah(new_track.tlwh))
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        if new_id:
            self.track_id = self.next_id()
        self.score = new_track.score

    def update(self, new_track, frame_id):
        """
        Update a matched track
        :type new_track: STrack
        :type frame_id: int
        :type update_feature: bool
        :return:
        """
        self.frame_id = frame_id
        self.tracklet_len += 1

        new_tlwh = new_track.tlwh
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyah(new_tlwh))
        self.state = TrackState.Tracked
        self.is_activated = True

        self.score = new_track.score

    @property
    # @jit(nopython=True)
    def tlwh(self):
        """Get current position in bounding box format `(top left x, top left y,
                width, height)`.
        """
        if self.mean is None:
            return self._tlwh.copy()
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    # @jit(nopython=True)
    def tlbr(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    @property
    # @jit(nopython=True)
    def xyah(self):
        """Convert bounding box to format `(center x, center y, aspect ratio,
        height)`, where the aspect ratio is `width / height`.
        """
        ret = self.tlwh.copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    @staticmethod
    # @jit(nopython=True)
    def tlwh_to_xyah(tlwh):
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    @staticmethod
    # @jit(nopython=True)
    def tlbr_to_tlwh(tlbr):
        ret = np.asarray(tlbr).copy()
        ret[2:] -= ret[:2]
        return ret

    @staticmethod
    # @jit(nopython=True)
    def tlwh_to_tlbr(tlwh):
        ret = np.asarray(tlwh).copy()
        ret[2:] += ret[:2]
        return ret

    def __repr__(self):
        return 'OT_{}_({}-{})'.format(self.track_id, self.start_frame, self.end_frame)


class BYTETracker(object):
    def __init__(self, track_thresh=0.5, track_buffer=30, match_thresh=0.8, min_box_area=10, frame_rate=30):
        self.tracked_stracks_history = [] # code by LSY
        self.tracked_stracks = []  # type: list[STrack]
        self.lost_stracks = []  # type: list[STrack]
        self.removed_stracks = []  # type: list[STrack]
        self.min_box_area=min_box_area

        self.frame_id = 0

        self.match_thresh = match_thresh
        self.track_thresh = track_thresh
        self.det_thresh = track_thresh + 0.1
        self.buffer_size = int(frame_rate / 30.0 * track_buffer)
        self.max_time_lost = self.buffer_size
        self.kalman_filter = KalmanFilter()

    def update(self, bboxes, scores, classes):
        '''
            <Step1. Get detection boxes from detector
                    & Sort out detection boxes using detection score and thresholds>

            architecture(bboxes, scores, classes): array([ [int], ... ])
            bboxes.shape = (n, 4), scores.shape = (n, 1), classes.shape = (n, 1)
            len(bboxes) = len(scores) = len(classes)

            architecture(*_stracks): [STrack, ...]
            architecture(det_low_idxes, det_high_idxes): array([boolean, ... ])
        '''
        # Initialize variables
        self.frame_id += 1
        scores=scores.reshape(-1) # scores.shape = (n,)
        classes=classes.reshape(-1) # classes.shape = (n,)

        tracked_stracks = []  # tracked stracks in current frame
        lost_stracks = []  # lost stracks in current frame
        removed_stracks = []  # removed stracks in current frame
        unconfirmed_stracks = []
        activated_starcks = []
        refind_stracks = []

        # Add newly detected tracklets to tracked_stracks
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed_stracks.append(track)
            else:
                tracked_stracks.append(track)
        strack_pool = joint_stracks(tracked_stracks, self.lost_stracks)

        # Sort out
        is_human = classes == 0
        low_idxes_low_limit = 0.1 < scores
        low_idxes_high_limit = scores <= self.track_thresh
        det_low_idxes = np.logical_and(low_idxes_low_limit, low_idxes_high_limit)
        det_low_human_idxes = np.logical_and(det_low_idxes, is_human)
        det_high_idxes = scores > self.track_thresh
        det_high_human_idxes = np.logical_and(det_high_idxes, is_human)

        # High detection threshold results
        bboxes_high = bboxes[det_high_human_idxes]
        scores_high = scores[det_high_human_idxes]
        classes_high = classes[det_high_human_idxes]

        # Low detection threshold results
        bboxes_low = bboxes[det_low_human_idxes]
        scores_low = scores[det_low_human_idxes]
        classes_low = classes[det_low_human_idxes]


        ''' <Step 2: Predict new locations of tracks> '''
        STrack.multi_predict(strack_pool)


        ''' 
            <Step 3: First association, with high score detection boxes>

            architecture(detections_high)
            architecture(dists_first): array([ [iou_distance, ...], ... ]) | dists_first.shape() = (n, n)
        '''
        # Detections | Stracks are __init__ step. So, STrack is just detection
        if len(bboxes_high) > 0:
            detections_high = [STrack(STrack.tlbr_to_tlwh(tlbr), s, cls) for (tlbr, s, cls) in zip(bboxes_high, scores_high, classes_high)]
        else:
            detections_high = []

        dists_first = matching.iou_distance(strack_pool, detections_high)
        dists_first = matching.fuse_score(dists_first, detections_high)
        matches_first, track_remain_idxes, detection_remain_idxes = matching.linear_assignment(dists_first, thresh=self.match_thresh)

        for track_idx, det_idx in matches_first:
            matched_track_high = strack_pool[track_idx]
            matched_det_high = detections_high[det_idx]
            if matched_track_high.state == TrackState.Tracked:
                matched_track_high.update(matched_det_high, self.frame_id)
                activated_starcks.append(matched_track_high)
            else:
                matched_track_high.re_activate(matched_det_high, self.frame_id, new_id=False)
                refind_stracks.append(matched_track_high)


        ''' <Step 4: Second association, with low score detection boxes> '''
        # Detections | Stracks are __init__ step. So, STrack is just detection
        if len(bboxes_low) > 0:
            detections_low = [STrack(STrack.tlbr_to_tlwh(tlbr), s, cls) for (tlbr, s, cls) in zip(bboxes_low, scores_low, classes_low)]
        else:
            detections_low = []
        
        stracks_remain = [strack_pool[idx] for idx in track_remain_idxes if strack_pool[idx].state == TrackState.Tracked]
        dists_second = matching.iou_distance(stracks_remain, detections_low)
        matches_second, track_re_remain_idxes, detection_re_remain_idxes = matching.linear_assignment(dists_second, thresh=0.5)

        for track_idx, det_idx in matches_second:
            matched_track_remain = stracks_remain[track_idx]
            matched_det_low = detections_low[det_idx]
            if matched_track_remain.state == TrackState.Tracked:
                matched_track_remain.update(matched_det_low, self.frame_id)
                activated_starcks.append(matched_track_remain)
            else:
                matched_track_remain.re_activate(matched_det_low, self.frame_id, new_id=False)
                refind_stracks.append(matched_track_remain)

        for idx in track_re_remain_idxes:
            track_re_remain = stracks_remain[idx]
            if not track_re_remain.state == TrackState.Lost:
                track_re_remain.mark_lost()
                lost_stracks.append(track_re_remain)


        ''' <Step 5: Delete unmatched tracks> '''
        for track in self.lost_stracks:
            if self.frame_id - track.end_frame > self.max_time_lost:
                track.mark_removed()
                removed_stracks.append(track)


        ''' Step 6: Initialize new tracks '''
        # Deal with unconfirmed tracks, usually tracks with only one beginning frame'''
        detections_remain = [detections_high[idx] for idx in detection_remain_idxes]
        dists_unconfirm = matching.iou_distance(unconfirmed_stracks, detections_remain)
        dists_unconfirm = matching.fuse_score(dists_unconfirm, detections_remain)
        matches_begin, u_unconfirmed, u_detection = matching.linear_assignment(dists_unconfirm, thresh=0.7)

        for track_idx, det_idx in matches_begin:
            matched_track_begin = unconfirmed_stracks[track_idx]
            matched_det_begin = detections_remain[det_idx]
            matched_track_begin.update(matched_det_begin, self.frame_id)
            activated_starcks.append(matched_track_begin)

        for it in u_unconfirmed:
            track = unconfirmed_stracks[it]
            track.mark_removed()
            removed_stracks.append(track)

        for inew in u_detection:
            track = detections_remain[inew]
            if track.score < self.det_thresh:
                continue
            track.activate(self.kalman_filter, self.frame_id)
            activated_starcks.append(track)

        self.tracked_stracks = [t for t in self.tracked_stracks if t.state == TrackState.Tracked]
        self.tracked_stracks = joint_stracks(self.tracked_stracks, activated_starcks)
        self.tracked_stracks = joint_stracks(self.tracked_stracks, refind_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.tracked_stracks)
        self.lost_stracks.extend(lost_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.removed_stracks)
        self.removed_stracks.extend(removed_stracks)
        self.tracked_stracks, self.lost_stracks = remove_duplicate_stracks(self.tracked_stracks, self.lost_stracks)

        STrack.record_center_point(self.frame_id, self.tracked_stracks)
        STrack.init_switch_action_state(self.tracked_stracks)
        STrack.init_overlap(self.tracked_stracks)
        STrack.check_overlap(self.tracked_stracks)
        
        # Create tracked_stracks_history
        '''
            architecture(tracked_stracks_history):
                [
                    { 
                        'frame_id': frame_id, 'tracked_stracks_list': [current_ids, ...], 'appear_tracked_stracks_list': [appear_ids, ...], 'disap_tracked_stracks_list': [disap_ids, ...],
                        'switch_tracks': [switch_ids, ...], 'separation_stracks': [separation_ids, ...], 'merge_stracks': [merge_ids, ...]'
                    }, ...
                ]
        '''
        self.tracked_stracks_history.append({'frame_id': self.frame_id, 'tracked_stracks_list': self.tracked_stracks, 'appear_tracked_stracks_list': [],
                                            'disap_tracked_stracks_list': [], 'switch_stracks': [], 'separation_stracks': [], 'merge_stracks': []})

        if 2 <= self.frame_id:
            # Find appeared stracks in central area
            appear_tracked_stracks_list = list(set(self.tracked_stracks) - set(self.tracked_stracks_history[-2]['tracked_stracks_list']))
            appear_tracked_stracks_list = [
                appear_tracked_strack for appear_tracked_strack in appear_tracked_stracks_list 
                if (appear_tracked_strack.cls == 0
                    and is_not_boundary(appear_tracked_strack.xyah) == True)
                ]
            self.tracked_stracks_history[-1]['appear_tracked_stracks_list'] = appear_tracked_stracks_list

            # Find disappeared stracks in central area
            disap_tracked_stracks_list = list(set(self.tracked_stracks_history[-2]['tracked_stracks_list']) - set(self.tracked_stracks))
            disap_tracked_stracks_list = [
                disap_tracked_strack for disap_tracked_strack in disap_tracked_stracks_list 
                if (disap_tracked_strack.cls == 0
                    and is_not_boundary(disap_tracked_strack.xyah) == True)
                ]
            self.tracked_stracks_history[-1]['disap_tracked_stracks_list'] = disap_tracked_stracks_list
            
            # Judge ID switching & Separation using appeared tracks 
            for appear_tracked_strack in self.tracked_stracks_history[-1]['appear_tracked_stracks_list']:
                appear_tracked_strack_cp = (appear_tracked_strack.xyah[0], appear_tracked_strack.xyah[1])

                # ID switching 
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

                # Separation
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
                            if separated_strack.cls == 0 and 2 <= separated_strack.meta_label:
                                self.tracked_stracks_history[-1]['separation_stracks'].append(separated_strack)
                                separated_strack.meta_label -= 1
            
            # Judge Merge using disappeared tracks
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
                            if merged_strack.cls == 0 and (1 / merged_strack.xyah[2]) < 2.7:
                                self.tracked_stracks_history[-1]['merge_stracks'].append(merged_strack)
                                merged_strack.merge.append(disap_tracked_strack)
                                merged_strack.merge = list(set(merged_strack.merge))
                                merged_strack.meta_label += disap_tracked_strack.meta_label
                    disap_tracked_strack.meta_label = 1

        return self.tracked_stracks_history


def is_not_boundary(xyah):
    x = xyah[0]
    y = xyah[1]
    if 20 < x < 620 and 30 < y < 330:
        return True
    else:
        return False


def joint_stracks(tlista, tlistb):
    exists = {}
    res = []
    for t in tlista:
        exists[t.track_id] = 1
        res.append(t)
    for t in tlistb:
        tid = t.track_id
        if not exists.get(tid, 0):
            exists[tid] = 1
            res.append(t)
    return res


def sub_stracks(tlista, tlistb):
    stracks = {}
    for t in tlista:
        stracks[t.track_id] = t
    for t in tlistb:
        tid = t.track_id
        if stracks.get(tid, 0):
            del stracks[tid]
    return list(stracks.values())


def remove_duplicate_stracks(stracksa, stracksb):
    pdist = matching.iou_distance(stracksa, stracksb)
    pairs = np.where(pdist < 0.15)
    dupa, dupb = list(), list()
    for p, q in zip(*pairs):
        timep = stracksa[p].frame_id - stracksa[p].start_frame
        timeq = stracksb[q].frame_id - stracksb[q].start_frame
        if timep > timeq:
            dupb.append(q)
        else:
            dupa.append(p)
    resa = [t for i, t in enumerate(stracksa) if not i in dupa]
    resb = [t for i, t in enumerate(stracksb) if not i in dupb]
    return resa, resb