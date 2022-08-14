import datetime
import threading
import os

from decoder.CvDecoder import CvDecoder
from detector.tracker.byte_tracker.BYTETracker import BYTETracker
from detector.tracker.sort.Sort import Sort
from config import config
from utils.time_util import convert_framenumber2timestamp


class EdgeModuleManager:
    def __init__(self, settings, logger, celery_instance):
        self.frame_buffer = []
        self.streaming_url = ""
        self.streaming_type = "cctv"
        self.cam_id = "0"
        self.fps = 0
        self.extract_fps = 0
        self.decoder = None
        self.decoder_thread = None
        self.filter_frame_numbers = []
        self.object_model = None
        self.object_score_threshold = 0.0
        self.object_nms_threshold = 0.0
        self.trackers = []
        self.tracker_names = []
        self.tracker_params = {}
        self.event_models = []
        self.event_model_names = []
        self.event_models_params = {}
        self.logger = logger
        self.celery_instance = celery_instance
        self.__parse_settings(settings)

    @staticmethod
    def parse_tracker_params(tracker_options):
        tracker_names = tracker_options["tracker_names"]
        tracker_params = {}
        for tracker_name in tracker_options:
            tracker_option = tracker_options[tracker_name]
            if tracker_name == "byte_tracker":
                tracker_params["byte_tracker"] = {
                    "tracker_class": BYTETracker,
                    "tracker_name": tracker_name,
                    "score_threshold": float(tracker_option["score_threshold"]),
                    "track_threshold": float(tracker_option["track_threshold"]),
                    "track_buffer": int(tracker_option["track_buffer"]),
                    "match_threshold": float(tracker_option["match_threshold"]),
                    "min_box_area": int(tracker_option["min_box_area"]),
                    "frame_rate": int(tracker_option["frame_rate"])
                }
            elif tracker_name == "sort_tracker":
                tracker_params["sort_tracker"] = {
                    "tracker_class": Sort,
                    "tracker_name": "sort_tracker",
                    "score_threshold": float(tracker_option["score_threshold"]),
                    "max_age": int(tracker_option["max_age"]),
                    "min_hits": int(tracker_option["min_hits"])
                }
        return tracker_names, tracker_params

    @staticmethod
    def reformat_object_result(frame_number, fps, extract_fps, results):
        frame_name = "{0:06d}.jpg".format(frame_number)

        reformat_result = {
            "image_name": frame_name,
            "frame_number": int(frame_number / extract_fps * fps),
            "timestamp": str(convert_framenumber2timestamp(frame_number / extract_fps * fps, fps)),
            "results": []
        }
        reformat_result["results"].append({"detection_result": results})
        return reformat_result

    def __parse_settings(self, settings):
        self.streaming_url = settings["cctv_info"]["streaming_url"]
        self.streaming_type = settings["cctv_info"]["streaming_type"]
        self.cam_id = settings["cctv_info"]["cam_id"]
        self.extract_fps = int(settings["decode_option"]["fps"])

        self.object_model_name = settings["model"]["object_detection"]["model_name"]
        self.object_score_threshold = float(settings["model"]["object_detection"]["score_threshold"])
        self.object_nms_threshold = float(settings["model"]["object_detection"]["nms_threshold"])

        tracker_options = settings["model"]["tracker"]
        self.tracker_names, self.tracker_params = self.parse_tracker_params(tracker_options)
        self.event_model_names = settings["model"]["event"]["event_names"]
        self.event_model_params = settings["model"]["event"]["event_options"]

    def __generate_filter_numbers(self, extract_fps, fps):
        if extract_fps is not 0 and fps is not 0:
            tmp_nums = []
            for i in range(1, fps + 1):
                filter_num = int(i * (extract_fps / fps))
                if filter_num != 0 and filter_num not in tmp_nums:
                    tmp_nums.append(filter_num)
                    self.filter_frame_numbers.append(i)
            self.logger.info("Extract frame number is {}".format(str(self.filter_frame_numbers).replace("[", "").replace("]", "").replace(" ", "")))
            return True
        else:
            self.logger.info("There is wrong fps or extract fps(fps: {} / extract fps {})".format(fps, extract_fps))
            return False

    # Function of Decoder
    def load_decoder(self):
        self.decoder = CvDecoder(self.streaming_url)
        ret = self.decoder.load()
        if ret:
            self.logger.info("Streaming url is successfully loaded.")
            self.fps = self.decoder.fps
            ret = self.__generate_filter_numbers(self.extract_fps, self.fps)
            if not ret:
                return False
            return True
        else:
            self.logger.info("Streaming url loading is failed.")
            return False

    # Function of Load Object Detection Models
    def load_object_model(self):
        try:
            import pycuda.autoinit
            self.object_model = config.OBJECT_MODEL[self.object_model_name](
                model=self.object_model_name,
                score_threshold=self.object_score_threshold,
                nms_threshold=self.object_nms_threshold
            )
            self.logger.info("{} model is successfully loaded".format("Object detection(yolov4)"))
            return True
        except:
            return False

    # Function of Load Object Trackers
    def load_tracker(self):
        log = " "
        for tracker_name in config.TRACKER.keys():
            try:
                if tracker_name in self.tracker_names:
                    tracker_param = self.tracker_params[tracker_name]
                    tracker = config.TRACKER[tracker_name](tracker_param)
                    self.trackers.append(tracker)
                    self.logger.info("Tracker({}) is successfully loaded".format(tracker_name))
            except:
                log += tracker_name + " "
                self.logger.info("Tracker({}) loading is failded".format(tracker_name))
        if len(self.trackers) != len(self.tracker_params):
            return False, log
        else:
            return True, log

    # Function of Load Event Models
    def load_event_model(self):
        log = " "
        for event_model_name in config.EVENT_MODEL.keys():
            try:
                if event_model_name in self.event_model_names:
                    event_model = config.EVENT_MODEL[event_model_name](debug=True)
                    self.event_models.append(event_model)
                    self.logger.info("Event model({}) is successfully loaded".format(event_model_name))
            except:
                log += event_model_name + " "
                self.logger.info("Event model({}) loading is failded".format(event_model_name))
        if len(self.event_models) != len(self.event_model_names):
            return False, log
        else:
            return True, log

    # Run decoder
    def run_decoder(self):
        filter_frame_number = 0
        while True:
            ret, frame = self.decoder.read()
            filter_frame_number += 1

            if ret == False:
                break
            else:
                if filter_frame_number % self.fps == 0:
                    filter_frame_number = 0
                if filter_frame_number in self.filter_frame_numbers and frame is not None:
                    self.frame_buffer.append(frame)

    # Load all models
    def load_models(self):
        # Load object detection model
        self.celery_instance.update_state(state="PROGRESS", meta={"message": "Start to load object detection. - {}".format(self.object_model_name)})
        ret = self.load_object_model()
        if ret:
            message = "Object detection model({}) is successfully loaded.".format(self.object_model_name)
            self.celery_instance.update_state(state="PROGRESS", meta={"message": message})
        else:
            message = "Object detection model loading is failed.({})".format(self.object_model_name)
            self.celery_instance.update_state(state="FAILED", meta={"message": message})
            return

        # Load object trackers
        self.celery_instance.update_state(state="PROGRESS", meta={"message": "Start to load tracker.({})".format(str(self.tracker_names))})
        ret, log = self.load_tracker()
        if ret:
            message = "Trackers is successfully loaded."
            self.logger.info(message)
            self.celery_instance.update_state(state="PROGRESS", meta={"message": message})
        else:
            message = "Tracker detection model loading is failed."
            self.logger.info(message)
            self.celery_instance.update_state(state="FAILED", meta={"message": message})
            # return

        # Load event models
        ret, log = self.load_event_model()
        if ret:
            message = "Event detection model({}) is successfully loaded.".format(",".join(self.event_model_names))
            self.logger.info(message)
            self.celery_instance.update_state(state="PROGRESS", meta={"message": message})
        else:
            message = "Event detection model loading is failed.({})".format(log)
            self.celery_instance.update_state(state="FAILED", meta={"message": message})
            self.logger.info(message)
            return

    @staticmethod
    def define_object_result(frame_dir, frame_name, video_path, frame_number, extract_fps, fps, od_model_name):
        dict_result = dict()
        dict_result["image_path"] = os.path.join(frame_dir, frame_name)
        dict_result["cam_address"] = video_path
        dict_result["module"] = od_model_name
        dict_result["frame_number"] = int(frame_number / extract_fps * fps)
        dict_result["timestamp"] = str(convert_framenumber2timestamp(frame_number / extract_fps * fps, fps))
        dict_result["results"] = []
        return dict_result

    @staticmethod
    def define_event_result(video_path, frame_number, extract_fps, fps):
        event_result = dict()
        event_result["cam_address"] = video_path
        event_result["frame_number"] = int(frame_number / extract_fps * fps)
        event_result["timestamp"] = str(convert_framenumber2timestamp(frame_number / extract_fps * fps, fps))
        event_result["event_result"] = dict()
        return event_result

    def run(self):
        decoder_thread = threading.Thread(target=self.run_decoder, )
        decoder_thread.start()
        self.celery_instance.update_state(state="PROGRESS", meta={"message": "Decoder started"})

        frame_number = 0
        self.celery_instance.update_state(state="PROGRESS", meta={"message": "Detection started"})
        while True:
            if len(self.frame_buffer) > 0:
                frame = self.frame_buffer.pop(0)
                frame_info = {"frame": frame, "frame_number": int(frame_number / self.extract_fps * self.fps), "cam_id": self.cam_id}
                object_result = self.define_object_result("", str(frame_number), self.streaming_url, frame_number, self.extract_fps, self.fps, self.object_model_name)
                object_result["results"].append({"detection_result": self.object_model.inference_by_image(frame)})
                tracking_results = dict()

                for i, tracker in enumerate(self.trackers):
                    tracking_result = tracker.update(object_result.copy())
                    tracking_results[tracker.tracker_name] = tracking_result

                event_result = self.define_event_result(self.streaming_url, frame_number, self.extract_fps, self.fps)
                for i, event_model in enumerate(self.event_models):
                    if self.event_model_params[event_model.model_name]["tracker"] != "none":
                        tracking_result = tracking_results[self.event_model_params[event_model.model_name]["tracker"]]
                    else:
                        tracking_result = None
                    event_result["event_result"][event_model.model_name] = event_model.inference(
                        frame_info,
                        object_result,
                        tracking_result,
                        self.event_model_params[event_model.model_name]["score_threshold"]
                    )
                    event_model.merge_sequence(frame_info, 0)

                for event_model in self.event_models:
                    now = datetime.datetime.now()
                    if event_model.new_seq_flag == True and frame_number > self.fps: # 모듈 시작 직후 message 보내는 부분 방지
                        event_model.new_seq_flag = False
                        # communicator.send_event(event_model.model_name, now, "start", None)
                        self.logger.info("Send start time of {} event sequence({}) - frame number: {}".format(event_model.model_name, now, frame_number))
                    if len(event_model.frameseq) > 0:
                        sequence = event_model.frameseq.pop()
                        message = sequence
                        message["duration"] = (sequence["end_frame"] - sequence["start_frame"]) / self.fps
                        # communicator.send_event(event_model.model_name, now, "end", message)
                        self.logger.info("Send end time of {} event sequence({}) - frame number: {}".format(event_model.model_name, now, frame_number))
                frame_number += 1
            else:
                if not self.decoder.capture.isOpened():
                    self.celery_instance.update_state(state="FINISHED", meta={"message": "CCTV streaming is closed."})
                    break
