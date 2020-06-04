
# TODO
#   - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
#   - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
#     (전체 결과 예시 : [{'name': 'Dummy', 'result': []}, {'name': 'Dummy2', 'result': []}]})

import os
import json
import pdb
import numpy as np
import itertools

class FightDetection:
    model = None
    # result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        self.model_name = "FightDetection"
        self.history = []
        self.result = 0

    def analysis_from_json(self, od_result, json_file):


        #if too long
        if len(self.history) >= 10000:
            self.history = []

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


        # Rule 1) If two people are close to each other
        if dist_list:
            for dist_ in dist_list:
                if dist_ < 500:
                    self.history.append(1) #return true
                    self.result = 1
                    return self.result

        # Rule 2) Simple smoothing 
        if sum(self.history[-20:]) > 13:
            self.history.append(1) #return true
            self.result = 1
            return self.result

        self.history.append(0) #return false
        self.result = 0

        return self.result 
        # Rule 3) If ...
        # Rule 4) If ...
