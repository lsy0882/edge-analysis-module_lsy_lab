import os
import time
from detector.event.template.main import Event
from detector.event.wanderer.utils import *
from detector.event.wanderer.Sort import Sort

# Notice
# - Dummy class는 참고 및 테스트용이기 때문에 해당 class는 수정 또는 삭제하지 말고 참고만 해주시기 바랍니다.
# - 이미 정의된 함수 및 클래스 멤버 변수의 이름은 *****절대로**** 변경하지마세요.

class WandererEvent(Event):
    model = None
    result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False):
        super().__init__(debug)
        self.model_name = "wanderer"
        self.analysis_time = 0
        self.debug = debug
        self.history = []
        self.result = False
        self.tracking_threshold = 200
        self.wander_check_point = [-150,-100,-50]

        # TODO: __init__
        # - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
        # - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
        # - 위의 4개 변수(model_name, analysis_time, debug, result) 중 하나라도 삭제하면 동작이 안되니 유의해주시기 바랍니다.
        self.id_stack = [0, 0, 0, 0]
        self.wandering_id_list = []
        self.mot_tracker = Sort()
        self.temp_frame = 1


    def inference(self, frame_info, detection_result):
            frame = frame_info["frame"]
            frame_number = frame_info["frame_number"]

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

            frame = detection_result["frame_number"]
            detection_result = detection_result["results"][0]["detection_result"]
            result = {}
            det_list = []
            for info_ in detection_result:
                # print(info_['position'])
                dets = []
                if info_['label'][0]['description'] == "person":
                    dets.append(float(info_['position']['x']))
                    dets.append(float(info_['position']['y']))
                    dets.append(float(info_['position']['x'] + info_['position']['w']))
                    dets.append(float(info_['position']['y'] + info_['position']['h']))
                    # convert to [x1,y1,w,h] to [x1,y1,x2,y2]
                    dets.append(float(info_['label'][0]['score']))
                    det_list.append(dets)

            trackers = self.mot_tracker.update(det_list)  # output : track_id, x1,y1,x2,y2
            # print('%d,%d,%.2f,%.2f,%.2f,%.2f'%(frame,trackers[4],trackers[0],trackers[1],trackers[2]-trackers[0],trackers[3]-trackers[1]))
            # print(trackers[:,4])
            # rule 1
            self.result = False
            for d in trackers:
                # print("id : {}".format(d[4]))
                while len(self.id_stack) <= d[4]:
                    self.id_stack.append(0)
                # previous_id_stack = copy.deepcopy(self.id_stack)

                self.id_stack[int(d[4])] += 1
                # detect Wander
                result["frame"]= int(frame)
                result["event"] = "no"
                list_check = True
                count50 = 0
                if self.id_stack[int(d[4])] >= self.tracking_threshold:
                    # if previous_id_stack[int(d[4])]!=self.id_stack[int(d[4])]:
                    result["event"] = "wander"
                    # result["frame"] = int(frame)
                    result["id_num"] = int(d[4])
                    result["id_count"] = self.id_stack[int(d[4])]
                    # print("wander frame : {}, id_num : {}, id_count {}".format(frame,int(d[4]), self.id_stack[int(d[4])]))
                    
                    for i in self.wander_check_point:
                        if self.history[i]["event"] != "wander":
                            list_check = False
                            break
                    
                    for i in range(1,60):
                        if self.history[-i]["event"] == "wander":
                            count50 +=1                    
#                     if self.history[-3]["event"]=="wander" and self.history[-2]["event"]=="wander" and self.history[-1]["event"]=="wander" and self.history[-50]["event"]=="wander":
#                         self.result = True
                if list_check == True and count50>=50:
                    self.result = True
                    # print(self.result)
                self.history.append(result)
            # TODO: analysis(끝 지점)

            if self.debug :
                end = time.time()
                self.analysis_time = end - start

            return self.result


    def merge_sequence(self,frame_info):
        self.frameseq = super().merge_sequence(frame_info)
        wanderer_frame_seq = self.frameseq
        if len(wanderer_frame_seq) >= 2:
            back_start = wanderer_frame_seq[-1]['start']
            back_end = wanderer_frame_seq[-1]['end']
            front_start = wanderer_frame_seq[-2]['start']
            front_end = wanderer_frame_seq[-2]['end']
            gap = back_start - front_end
            if gap < 200:
                del wanderer_frame_seq[-2:]
                merged_seq = {}
                merged_seq['start'] = front_start
                merged_seq['end'] = back_end
                wanderer_frame_seq.append(merged_seq)
            else: 
                pass
        self.frameseq = wanderer_frame_seq
        return self.frameseq
