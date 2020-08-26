from Modules.tailing_kidnapping.main import Tailing_Kidnapping
from Modules.obstacle.main import Obstacle
from Modules.FightDetection.main import FightDetection
from Modules.WanderDetection.main import WanderDetection
from threading import Thread
import socket
from datetime import datetime
import ast
import json
import cv2
import json
import os
import numpy

class EventDetector:
    def __init__(self, debug=False, display=False, show_scale=1, metadata=""):
        self.debug = debug
        self.display = display
        self.show_scale = show_scale
        if metadata != "" :
            with open(metadata) as json_file:
                self.metadata = json.load(json_file)
        else :
            self.metadata = None
        self.current_event = None
        self.current_event_index = 0

        self.models = []

        fight_detection_model = FightDetection(self.debug)
        print("INFO: {} - {} model is loaded".format(datetime.now(), fight_detection_model.model_name))

        wander_detection_model = WanderDetection(self.debug)
        print("INFO: {} - {} model is loaded".format(datetime.now(), wander_detection_model.model_name))

        obstacle_model = Obstacle(self.debug)
        print("INFO: {} - {} model is loaded".format(datetime.now(), obstacle_model.model_name))

        tailing_kidnapping_model = Tailing_Kidnapping(self.debug)
        print("INFO: {} - {} model is loaded".format(datetime.now(), tailing_kidnapping_model.model_name))

        self.models.append(fight_detection_model)
        self.models.append(wander_detection_model)
        self.models.append(obstacle_model)
        self.models.append(tailing_kidnapping_model)
        print("INFO: {} - Server is Initialized".format(datetime.now()))

    def detect_event(self, od_result):
        json_data = od_result

        threads = []
        for model in self.models:
            thread = Thread(target=model.analysis_from_json, args=(json_data,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        results = {
            "frame_num": od_result["frame_num"],
            "results": []
        }

        for model in self.models:
            result = {
                "name": model.model_name,
                "time": model.analysis_time,
                "result": model.result
            }
            results["results"].append(result)
        return results
