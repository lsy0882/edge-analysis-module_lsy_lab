import os

import json
from collections import OrderedDict

class Obstacle:
    model = None
    result = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):

        self.model_name = "Obstacle"
        #검출대상(보행장애물)
        self.target = ['car', 'truck', 'bus', 'motorcycle', 'bicycle', 'scooter', 
                    'movable_signage', 'potted_plant', 'bollard', 'chair', 'carrier']

    def analysis_from_json(self, od_result):

        # result json - image_path, cam_id, frame_num, detected_categories(label, score, center_coordinates)

        received = od_result.decode('utf-8').replace("'", '"')
        data = json.loads(received)

        resultJson = OrderedDict()
        detected_categories = []

        for i, e in enumerate(data['results'][0]['detection_result']):
            if e['label'][0]['description'] in self.target:
                obstacles = OrderedDict()
                obstacles["label"] = e['label'][0]['description'] 
                obstacles["score"] = e['label'][0]['score']
                obstacles["center_coordinates"] = ( (e['position']['x'] + e['position']['w'])/2, (e['position']['y'] + e['position']['h'])/2 )
                detected_categories.append(obstacles)

        resultJson["image_path"] = data["image_path"]
        resultJson["modules"] = data["modules"]
        resultJson["cam_id"] = data["cam_id"]
        resultJson["frame_num"] = data["frame_num"]
        resultJson["detected_obstacle"] = detected_categories

        result = json.dumps(resultJson)
        self.result = result

        return self.result