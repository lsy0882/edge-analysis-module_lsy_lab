import os

import json
from collections import OrderedDict

class Tailing_Kidnapping:
    model = None
    result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        self.model_name = "Tailing_Kidnapping"
        self.target = ['person']

    def analysis_from_json(self, od_result):

        received = od_result.decode('utf-8').replace("'", '"')
        data = json.loads(received)

        resultJson = OrderedDict()
        detected_person = []

        for i, e in enumerate(data['results'][0]['detection_result']):
            if e['label'][0]['description'] in self.target:
                person = OrderedDict()
                person["id"] = i+1  # id는 1부터 시작
                person["center_coordinates"] =  ( (e['position']['x'] + e['position']['w'])/2, (e['position']['y'] + e['position']['h'])/2 )
                detected_person.append(person)

        resultJson["image_path"] = data["image_path"]
        resultJson["modules"] = data["modules"]
        resultJson["cam_id"] = data["cam_id"]
        resultJson["frame_num"] = data["frame_num"]
                
        if len(detected_person) >=2 : # 보행자가 2명 이상 검출되면 미행 및 납치 상황 의심
            resultJson["state"] = "suspect"
            resultJson["detected_person"] = detected_person # 검출된 보행자의 정보
        else :
            resultJson["state"] = "safe"

        result = json.dumps(resultJson)
        self.result = result

        return self.result