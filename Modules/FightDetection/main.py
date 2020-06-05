
# TODO
#   - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
#   - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
#     (전체 결과 예시 : [{'name': 'Dummy', 'result': []}, {'name': 'Dummy2', 'result': []}]})
import time
import os
import json
import numpy as np
import itertools

class FightDetection:
    model = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug):
        self.model_name = "FightDetection"

    def analysis_from_json(self, od_result):
        self.result = "safe"
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        od_result = od_result.decode('utf-8').replace("'", '"')
        od_result = json.loads(od_result)
        #if too long

        position_list = []
        dist_list = []
        dist_flag = 0

        detection_result = od_result['results'][0]['detection_result']
        for info_ in detection_result:

            if info_['label'][0]['description'] == 'person' and info_['label'][0]['score'] > 0.65:
                pt_ = np.asarray([info_['position']['x']+info_['position']['w']/2, info_['position']['y']+info_['position']['h']/2])
                position_list.append(pt_)


        combinations_ = list(itertools.combinations(position_list, 2))

        for pt_ in combinations_:
            dist_ = np.linalg.norm(pt_[0] - pt_[1])
            dist_list.append(dist_)

        if self.debug :
            end = time.time()
            self.analysis_time = end - start

        # Rule 1) If two people are close to each other
        if dist_list:
            for dist_ in dist_list:
                if dist_ < 500:
                  
        # Rule 3) If ...
        # Rule 4) If ...
