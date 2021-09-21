import os
import time

# Notice
# - Dummy class는 참고 및 테스트용이기 때문에 해당 class는 수정 또는 삭제하지 말고 참고만 해주시기 바랍니다.
# - 이미 정의된 함수 및 클래스 멤버 변수의 이름은 *****절대로**** 변경하지마세요.

class Event:
    def __init__(self, debug=False):
        self.analysis_time = 0
        self.debug = debug
        self.result = False
        self.frameseq = []
        self.r_value = False
        self.frameseq_info = {"start": 0, "end": 1}
        self.model_name = "dummy"
        self.new_seq_flag = False

        # TODO: __init__
        # - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
        # - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
        # - 위의 7개 변수(model_name, analysis_time, debug, result, frameseq, r_value, frameseq_info) 중 하나라도 삭제하면 동작이 안되니 유의해주시기 바랍니다.

    def inference(self, frame_info, detection_result):
        frame = frame_info["frame"]
        frame_number = frame_info["frame_number"]
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        # TODO: analysis
        # - 분석에 필요한 내용을 작성해주실 부분입니다.
        # - 마지막 라인(return self.result)는 테스트 코드에서 확인하기 위한 코드이며 실제로는 thread에서 사용하지 않습니다.
        #   따라서 반드시 결과 값은 self.result에 저장하시기 바라며, 마지막 라인은 변경하지 마시기 바랍니다.
        # - 이전 프레임의 결과를 사용해야하는 모듈들의 경우 self.history에 저장한 후 사용하시기 바랍니다.
        # - self.result에는 True 또는 False 값으로 이벤트 검출 결과를 저장해주시기 바랍니다.

        if self.debug :
            end = time.time()
            self.analysis_time = end - start


        return self.result

    def merge_sequence(self, frame_info, end_flag):
        frame_number = frame_info["frame_number"]
        if self.result is True:
            if self.r_value is True:  # TT인 경우
                self.frameseq_info["end"] = frame_number
                if end_flag is 1:
                    self.frameseq.append(self.frameseq_info)
            else:  # FT인 경우
                self.new_seq_flag = True
                self.frameseq_info["start"] = frame_number
                self.frameseq_info["end"] = frame_number

        else:
            if self.r_value is True:  # TF인경우
                self.frameseq.append(self.frameseq_info)
                self.frameseq_info = {"start": 0, "end": 0}
            if self.r_value is False:  # FF인경우
                pass

        self.r_value = self.result
        return self.frameseq

    def get_new_seq_flag(self):
        return self.new_seq_flag

    def set_new_seq_flag(self, value):
        self.new_seq_flag = value