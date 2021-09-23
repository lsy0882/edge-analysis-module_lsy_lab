import datetime
import json
import os
import threading
import time
from decoder.FFmpegDecoder import FFmpegDecoder
from detector.event.assault.main import AssaultEvent
from detector.event.falldown.main import FalldownEvent
from detector.event.kidnapping.main import KidnappingEvent
from detector.event.obstacle.main import ObstacleEvent
from detector.event.tailing.main import TailingEvent
from detector.event.wanderer.main import WandererEvent
from detector.object_detection.yolov4 import YOLOv4
from communicator.communicator import Communicator
from utils import Logging

import pycuda.autoinit


class EdgeModule:
    path = os.path.dirname(os.path.abspath(__file__))
    event_model_class = {
        "assault": AssaultEvent,
        "falldown": FalldownEvent,
        "kidnapping": KidnappingEvent,
        "tailing": TailingEvent,
        "wanderer": WandererEvent,
        "obstacle": ObstacleEvent
    }

    def __init__(self):
        ret = self.load_settings()
        ret = self.load_models()
        self.message_pool = []
        self.frame_buffer = []
        self.communicator = Communicator(self.communication_info, self.streaming_url, self.message_pool)

    def load_settings(self):
        try:
            setting_path = os.path.join(self.path, "settings.json")
            with open(setting_path, 'r') as setting_file:
                dict_settings = json.load(setting_file)
                setting_file.close()
            streaming_url, fps, communication_info, od_option, event_option = self.__parse_settings(dict_settings)
            self.streaming_url = streaming_url
            self.fps = fps
            self.communication_info = communication_info
            self.od_option = od_option
            self.event_option = event_option
            self.load_decoder()
            self.decoder_thread = None
            return True
        except :
            print(Logging.e("Cannot load setting.json"))
            exit(0)

    def __parse_settings(self, dict_settings):
        streaming_url = dict_settings['streaming_url']
        fps = dict_settings['fps']
        communication_info = dict_settings['communication_info']
        od_option = dict_settings['model']['object_detection']
        event_option = dict_settings['model']['event']

        print(Logging.i("Settings INFO"))
        print(Logging.s("Streaming URL\t\t\t: {}".format(streaming_url)))
        print(Logging.s("Extract FPS\t\t\t: {}".format(fps)))
        print(Logging.s("Communication info:"))
        print(Logging.s("\tServer URL\t\t: {}:{}".format(communication_info['server_url']['ip'], communication_info['server_url']['port'])))
        print(Logging.s("\tMessage Size\t\t: {}".format(communication_info['message_size'])))
        print(Logging.s("Object detection model INFO: "))
        print(Logging.s("\tModel name\t\t: {}".format(od_option['model_name'])))
        print(Logging.s("\tScore Threshold\t\t: {}".format(od_option['score_thresh'])))
        print(Logging.s("\tNMS Threshold\t\t: {}".format(od_option['nms_thresh'])))
        print(Logging.s("Event model INFO: "))
        print(Logging.s("\tModels\t\t\t: {}".format(event_option)))

        return streaming_url, fps, communication_info, od_option, event_option

    def load_decoder(self):
        self.decoder = FFmpegDecoder(self.streaming_url, fps=self.fps)
        self.decoder.load()

    def run_decoder(self):
        while True:
            ret, frame = self.decoder.read()
            if ret == False:
                break
            else:
                self.frame_buffer.append(frame)

    def load_models(self):
        od_model_name = self.od_option["model_name"]
        score_thresh = self.od_option["score_thresh"]
        nms_thresh = self.od_option["nms_thresh"]
        try :
            if od_model_name == "yolov4-416":
                od_model = YOLOv4(model=od_model_name, score_threshold=score_thresh, nms_threshold=nms_thresh)
            else:
                od_model = YOLOv4(model=od_model_name, score_threshold=score_thresh, nms_threshold=nms_thresh)
            self.od_model = od_model
            print(Logging.i("{} model is loaded".format(od_model_name)))
        except:
            print(Logging.e("Cannot load object detection model({})".format(od_model_name)))
            exit(0)

        event_models = []
        event_model_names = self.event_option
        for event_model_name in event_model_names:
            try:
                event_model = self.event_model_class[event_model_name](debug=True)
                event_models.append(event_model)
                print(Logging.i("{} model is loaded".format(event_model.model_name)))
            except:
                print(Logging.e("Cannot load event detection model({})".format(event_model_name)))
                exit(0)

        self.event_models = event_models

        return True


    def run_detection(self):
        process_framecount = 0
        process_time = 0

        frame_number = 1
        self.decoder_thread = threading.Thread(target=self.run_decoder,)
        self.decoder_thread.start()

        while True:
            if len(self.frame_buffer) > 0 :
                frame = self.frame_buffer.pop(0)
                start_time = time.time()

                frame_info = {"frame": frame, "frame_number": frame_number}
                results = self.od_model.inference_by_image(frame)

                dict_result = dict()
                dict_result["frame_number"] = frame_number
                dict_result["results"] = []
                dict_result["results"].append({"detection_result": results})

                for event_model in self.event_models:
                    event_model.inference(frame_info, dict_result)
                    event_model.merge_sequence(frame_info, 0)

                for event_model in self.event_models:
                    now = datetime.datetime.now()
                    if event_model.new_seq_flag == True:
                        event_model.new_seq_flag = False
                        self.communicator.send_event(event_model.model_name, now, "start", None)
                        print(Logging.d("Send start time of {} event sequence({})".format(event_model.model_name, now)))
                    if len(event_model.frameseq) > 0:
                        sequence = event_model.frameseq.pop()
                        message = sequence
                        message["duration"] = (sequence["end_frame"] - sequence["start_frame"])/self.fps
                        self.communicator.send_event(event_model.model_name, now, "end", message)
                        print(Logging.d("Send start time of {} event sequence({})".format(event_model.model_name, now)))

                frame_number += 1

                end_time = time.time()
                process_time += (end_time - start_time)
                process_framecount += 1

                print(Logging.d("frame number: {:>6}\t|\tprocess fps: {:>5}\t|\tframe buffer: {}\t|\t"
                    .format(
                        frame_number,
                        round(process_framecount / process_time, 3),
                        len(self.frame_buffer)
                    )))


    def __del__(self):
        now = datetime.datetime.now()
        self.communicator.send_event(None, now, "disconnect", None)

if __name__ == '__main__':
    main = EdgeModule()
    main.run_detection()