import numpy as np
import copy

from .kalman_filter import KalmanFilter
from . import matching
from .basetrack import BaseTrack, TrackState
from itertools import combinations


class STrack(BaseTrack):
    shared_kalman = KalmanFilter()
    def __init__(self, tlwh, score, cls):
        self._tlwh = np.asarray(tlwh, dtype=np.float)
        self.score = score
        self.cls=cls
        self.kalman_filter = None
        self.mean, self.covariance = None, None
        self.is_activated = False
        self.tracklet_len = 0
        self.cp = []
        self.overlap = []
        self.merge = []
        self.meta_label = 1
        self.switch_state = False 
        self.action_state = None

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
        self.kalman_filter = kalman_filter
        self.track_id = self.next_id()
        self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xyah(self._tlwh))

        self.tracklet_len = 0
        self.state = TrackState.Tracked
        if frame_id == 1:
            self.is_activated = True
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
        self.frame_id = frame_id
        self.tracklet_len += 1

        new_tlwh = new_track.tlwh
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyah(new_tlwh))
        self.state = TrackState.Tracked
        self.is_activated = True

        self.score = new_track.score

    @property
    def tlwh(self):
        if self.mean is None:
            return self._tlwh.copy()
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    def tlbr(self):
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    @property
    def xyah(self):
        ret = self.tlwh.copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    @staticmethod
    def tlwh_to_xyah(tlwh):
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    @staticmethod
    def tlbr_to_tlwh(tlbr):
        ret = np.asarray(tlbr).copy()
        ret[2:] -= ret[:2]
        return ret

    @staticmethod
    def tlwh_to_tlbr(tlwh):
        ret = np.asarray(tlwh).copy()
        ret[2:] += ret[:2]
        return ret

    def __repr__(self):
        return 'OT_{}_({}-{})'.format(self.track_id, self.start_frame, self.end_frame)


class BYTETracker(object):
    def __init__(self, track_thresh=0.5, track_buffer=30, match_thresh=0.8, min_box_area=10, frame_rate=30):
    
        self.tracked_stracks = []
        self.lost_stracks = []
        self.removed_stracks = []
        self.min_box_area=min_box_area

        self.frame_id = 0

        self.match_thresh = match_thresh
        self.track_thresh = track_thresh
        self.det_thresh = track_thresh + 0.1
        self.buffer_size = int(frame_rate / 30.0 * track_buffer)
        self.max_time_lost = self.buffer_size
        self.kalman_filter = KalmanFilter()

    def update(self, bboxes, scores, classes):
        self.frame_id += 1
        scores=scores.reshape(-1)
        classes=classes.reshape(-1)

        tracked_stracks = []
        lost_stracks = []
        removed_stracks = []
        unconfirmed_stracks = []
        activated_starcks = []
        refind_stracks = []

        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed_stracks.append(track)
            else:
                tracked_stracks.append(track)
        strack_pool = joint_stracks(tracked_stracks, self.lost_stracks)

        is_human = classes == 0
        low_idxes_low_limit = 0.1 < scores
        low_idxes_high_limit = scores <= self.track_thresh
        det_low_idxes = np.logical_and(low_idxes_low_limit, low_idxes_high_limit)
        det_low_human_idxes = np.logical_and(det_low_idxes, is_human)
        det_high_idxes = scores > self.track_thresh
        det_high_human_idxes = np.logical_and(det_high_idxes, is_human)

        bboxes_high = bboxes[det_high_human_idxes]
        scores_high = scores[det_high_human_idxes]
        classes_high = classes[det_high_human_idxes]

        bboxes_low = bboxes[det_low_human_idxes]
        scores_low = scores[det_low_human_idxes]
        classes_low = classes[det_low_human_idxes]


        STrack.multi_predict(strack_pool)


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


        for track in self.lost_stracks:
            if self.frame_id - track.end_frame > self.max_time_lost:
                track.mark_removed()
                removed_stracks.append(track)


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

        return self.tracked_stracks


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