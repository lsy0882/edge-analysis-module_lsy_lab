import os
import time
import itertools
import numpy as np
from detector.event.template.main import Event

# Notice
# - Dummy class는 참고 및 테스트용이기 때문에 해당 class는 수정 또는 삭제하지 말고 참고만 해주시기 바랍니다.
# - 이미 정의된 함수 및 클래스 멤버 변수의 이름은 *****절대로**** 변경하지마세요.

class AssaultEvent(Event):
    model = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False):
        super().__init__(debug)
        self.model_name = "assault"
        self.history = []
        self.debug = debug
        self.result = 0
        self.analysis_time = 0

        # TODO: __init__
        # - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
        # - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
        # - 위의 4개 변수(model_name, analysis_time, debug, result) 중 하나라도 삭제하면 동작이 안되니 유의해주시기 바랍니다.

    def inference(self, detection_result):
        self.result = "safe"
        start = 0
        end = 0

        if self.debug :
            start = time.time()

        # TODO: analysis(시작 지점)
        # - 분석에 필요한 내용을 작성해주실 부분입니다.
        # - 마지막 라인(return self.result)는 테스트 코드에서 확인하기 위한 코드이며 실제로는 thread에서 사용하지 않습니다.
        #   따라서 반드시 결과 값은 self.result에 저장하시기 바라며, 마지막 라인은 변경하지 마시기 바랍니다.
        # - 이전 프레임의 결과를 사용해야하는 모듈들의 경우 self.history에 저장한 후 사용하시기 바랍니다.

        if len(self.history) >= 10000:
            self.history = []

        position_list = []
        dist_list = []
        dist_flag = 0

        detection_result = detection_result['results'][0]['detection_result']
        for info_ in detection_result:

            if info_['label'][0]['description'] == 'person' and info_['label'][0]['score'] > 0.65:
                pt_ = np.asarray([info_['position']['x'] + info_['position']['w'] / 2,
                                  info_['position']['y'] + info_['position']['h'] / 2])
                position_list.append(pt_)

        combinations_ = list(itertools.combinations(position_list, 2))

        for pt_ in combinations_:
            dist_ = np.linalg.norm(pt_[0] - pt_[1])
            dist_list.append(dist_)

        self.result = 0

        # Rule 1) If two people are close to each other
        if dist_list:
            for dist_ in dist_list:
                if dist_ < 40:
                    self.history.append(1)  # return true
                    self.result = 1
                    return self.result

        # Rule 2) Simple smoothing
        if sum(self.history[-20:]) > 2:
            self.history.append(0)
            self.result = 1
            return self.result

        self.history.append(0)
        self.result = 0

        # TODO: analysis(끝 지점)

        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        return self.result