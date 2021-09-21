import datetime
import json
import os
import time

from decoder.FFmpegDecoder import FFmpegDecoder
from detector.event.assault.main import AssaultEvent
from detector.event.falldown.main import FalldownEvent
from detector.event.kidnapping.main import KidnappingEvent
from detector.event.obstacle.main import ObstacleEvent
from detector.event.tailing.main import TailingEvent
from detector.event.wanderer.main import WandererEvent
from detector.object_detection.yolov4 import YOLOv4

from utils import Logging
import pycuda.autoinit

path = os.path.dirname(os.path.abspath(__file__))


class Main:
    def __init__(self):
        ret = self.load_settings()
        ret = self.load_models()

    def load_settings(self):
        try:
            setting_path = os.path.join(path, "settings.json")
            with open(setting_path, 'r') as setting_file:
                dict_settings = json.load(setting_file)
                setting_file.close()
            streaming_url, fps, server_url, od_option, event_option, reset_duration = self.__parse_settings(dict_settings)
            self.streaming_url = streaming_url
            self.fps = fps
            self.server_url = server_url
            self.od_option = od_option
            self.event_option = event_option
            self.reset_duration = reset_duration

            return True
        except :
            print(Logging.e("Cannot load setting.json"))
            exit(0)

    def __parse_settings(self, dict_settings):
        streaming_url = dict_settings['streaming_url']
        fps = dict_settings['fps']
        server_url = dict_settings['server_url']
        od_option = dict_settings['model']['object_detection']
        event_option = dict_settings['model']['event']
        reset_duration = dict_settings['reset_duration']

        print(Logging.i("Settings INFO"))
        print(Logging.s("Streaming URL\t\t\t: {}".format(streaming_url)))
        print(Logging.s("Extract FPS\t\t\t: {}".format(fps)))
        print(Logging.s("Server URL\t\t\t: {}:{}".format(server_url['ip'], server_url['port'])))
        print(Logging.s("Reset duration\t\t\t: {} days").format(reset_duration))
        print(Logging.s("Object detection model INFO: "))
        print(Logging.s("\tModel name\t\t: {}".format(od_option['model_name'])))
        print(Logging.s("\tScore Threshold\t\t: {}".format(od_option['score_thresh'])))
        print(Logging.s("\tNMS Threshold\t\t: {}".format(od_option['nms_thresh'])))
        print(Logging.s("Event model INFO: "))
        print(Logging.s("\tModels\t\t\t: {}".format(event_option)))

        return streaming_url, fps, server_url, od_option, event_option, reset_duration


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
        except:
            print(Logging.e("Cannot load object detection model({})".format(od_model_name)))
            exit(0)

        event_models = []
        event_model_class = {
            "assault": AssaultEvent,
            "falldown": FalldownEvent,
            "kidnapping": KidnappingEvent,
            "tailing": TailingEvent,
            "wanderer": WandererEvent,
            "obstacle": ObstacleEvent}
        event_model_names = self.event_option
        for event_model_name in event_model_names:
            try:
                event_model = event_model_class[event_model_name](debug=True)
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

        decoder = FFmpegDecoder(self.streaming_url, fps=self.fps)
        decoder.load()

        while True:
            start_time = time.time()
            ret, frame = decoder.read()
            if ret == False:
                break

            frame_name = "{0:06d}.jpg".format(frame_number)
            frame_info = {"frame": frame, "frame_number": frame_number}
            results = self.od_model.inference_by_image(frame)

            dict_result = dict()
            dict_result["image_path"] = frame_name
            dict_result["frame_number"] = frame_number
            dict_result["results"] = []
            dict_result["results"].append({"detection_result": results})

            for event_model in self.event_models:
                event_model.inference(frame_info, dict_result)
                event_model.merge_sequence(frame_info, 0)

            for event_model in self.event_models:
                if event_model.new_seq_flag == True:
                    # print("{}: start sequence".format(event_model.model_name), end='')
                    event_model.new_seq_flag = False
                    print(Logging.d("Send start time of {} event sequence({})".format(event_model.model_name, datetime.datetime.now())))
                    # Send start time of sequence
                if len(event_model.frameseq) > 0:
                    sequence = event_model.frameseq.pop()
                    # print(" / {}: {}".format(event_model.model_name, sequence), end='')
                    print(Logging.d("Send end time of {} event sequence({})".format(event_model.model_name, datetime.datetime.now())))
                    # Send end time of sequence
            frame_number += 1

            end_time = time.time()
            process_time += (end_time - start_time)
            process_framecount += 1

            print(Logging.d("frame number: {:>6}\t|\tprocess fps: {:>5}\t"
                  .format(frame_number,
                          round(process_framecount / process_time), 3)), end='')
            print("({:>10}: {:>5} / {:>10}: {:>5} / {:>10}: {:>5} / {:>10}: {:>5} / {:>10}: {:>5})"
                .format(
                self.event_models[0].model_name, round(self.event_models[0].analysis_time, 3),
                self.event_models[1].model_name, round(self.event_models[1].analysis_time, 3),
                self.event_models[2].model_name, round(self.event_models[2].analysis_time, 3),
                self.event_models[3].model_name, round(self.event_models[3].analysis_time, 3),
                self.event_models[4].model_name, round(self.event_models[4].analysis_time, 3),
            ))


if __name__ == '__main__':
    main = Main()

    main.run_detection()