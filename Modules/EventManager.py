import threading

from modules.assault.main import AssaultEvent
from modules.wanderer.main import WandererEvent
from modules.obstacle.main import ObstacleEvent
from modules.kidnapping.main import KidnappingEvent
from modules.tailing.main import TailingEvent
from modules.reid.main import ReidEvent
from utils import PrintLog


class EventManager:
    def __init__(self, object_detection_result_pool, final_result_pool):
        self.event_detectors = []
        self.final_result_pool = final_result_pool
        self.object_detection_result_pool = object_detection_result_pool
        fight_detection_model = AssaultEvent()
        PrintLog.i("{} model is loaded".format(fight_detection_model.model_name))

        wander_detection_model = WandererEvent()
        PrintLog.i("{} model is loaded".format(wander_detection_model.model_name))

        obstacle_model = ObstacleEvent()
        PrintLog.i("{} model is loaded".format(obstacle_model.model_name))

        kidnapping_model = KidnappingEvent()
        PrintLog.i("{} model is loaded".format(kidnapping_model.model_name))

        tailing_model = TailingEvent()
        PrintLog.i("{} model is loaded".format(kidnapping_model.model_name))

        reid_model = ReidEvent()
        PrintLog.i("{} model is loaded".format(kidnapping_model.model_name))

        self.event_detectors.append(fight_detection_model)
        self.event_detectors.append(wander_detection_model)
        self.event_detectors.append(obstacle_model)
        self.event_detectors.append(kidnapping_model)
        self.event_detectors.append(tailing_model)
        self.event_detectors.append(reid_model)

    def run(self):
        while True:
            if len(self.object_detection_result_pool) > 0:
                object_detection_result = self.object_detection_result_pool.pop(0)
                event_threads = []
                for event_detector in self.event_detectors:
                    event_thread = threading.Thread(target=event_detector.inference, args=(object_detection_result["results"],))
                    event_threads.append(event_thread)

                for thread in event_threads:
                    thread.start()

                for thread in event_threads:
                    thread.join()

                result = dict()
                result["cam_address"] = object_detection_result["cam_address"]
                result["timestamp"] = object_detection_result["timestamp"]
                result["event_result"] = dict()
                for event_detector in self.event_detectors:
                    result["event_result"][event_detector.model_name] = event_detector.result

                self.final_result_pool.append(result)