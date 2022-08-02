from detector.object_detection.yolov4.yolov4 import YOLOv4
from detector.event.assault.main import AssaultEvent
from detector.event.falldown.main import FalldownEvent
from detector.event.kidnapping.main import KidnappingEvent
from detector.event.tailing.main import TailingEvent
from detector.event.wanderer.main import WandererEvent
from module_manager import EdgeModuleManager
from utils.time_util import convert_framenumber2timestamp
from utils.setting_utils import *

import time
import datetime
import threading
import os
import cv2
from celery import Celery
from celery.utils.log import get_task_logger

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

app = Celery('tasks', broker=BROKER_URL, backend=CELERY_RESULT_BACKEND)
logger = get_task_logger(__name__)
current_task = None

def load_object_model(object_model_name, object_score_threshold, object_nms_threshold):
    object_model = None
    if object_model_name == "yolov4-416":
        import pycuda.autoinit

        object_model = YOLOv4(
            model=object_model_name,
            score_threshold=object_score_threshold,
            nms_threshold=object_nms_threshold
        )
        logger.info("{} model is loaded".format("Object detection(yolov4)"))
    return object_model


def load_event_model(model_names):
    event_models = []
    if "assault" in model_names:
        assault_detection_model = AssaultEvent()
        event_models.append(assault_detection_model)
        logger.info("{} model is loaded".format(assault_detection_model.model_name))

    if "falldown" in model_names:
        falldown_detection_model = FalldownEvent()
        event_models.append(falldown_detection_model)
        logger.info("{} model is loaded".format(falldown_detection_model.model_name))

    if "kidnapping" in model_names:
        kidnapping_detection_model = KidnappingEvent()
        event_models.append(kidnapping_detection_model)
        logger.info("{} model is loaded".format(kidnapping_detection_model.model_name))

    if "tailing" in model_names:
        tailing_detection_model = TailingEvent()
        event_models.append(tailing_detection_model)
        logger.info("{} model is loaded".format(tailing_detection_model.model_name))

    if "wanderer" in model_names:
        wanderer_detection_model = WandererEvent()
        event_models.append(wanderer_detection_model)
        logger.info("{} model is loaded".format(wanderer_detection_model.model_name))

    return event_models


def get_fps(video_url):
    capture = cv2.VideoCapture(video_url)
    fps = int(round(capture.get(cv2.CAP_PROP_FPS)))
    capture.release()
    return fps


def reformat_object_result(object_model_name, frame_number, fps, extract_fps, results):
    frame_name = "{0:06d}.jpg".format(frame_number)

    reformat_result = {
        "image_name": frame_name,
        "frame_number": int(frame_number / extract_fps * fps),
        "timestamp": str(convert_framenumber2timestamp(frame_number / extract_fps * fps, fps)),
        "results": []
    }
    reformat_result["results"].append({"detection_result": results})
    return reformat_result


def run_decoder(decoder, frame_buffer):
    while True:
        ret, frame = decoder.read()
        if ret == False:
            break
        else:
            frame_buffer.append(frame)


def generate_filter_nums(extract_fps, fps):
    filter_numbers = []
    tmp_nums = []
    for i in range(1, fps + 1):
        filter_num = int(i * (extract_fps / fps))
        if filter_num != 0 and filter_num not in tmp_nums:
            tmp_nums.append(filter_num)
            filter_numbers.append(i)

    return filter_numbers


@app.task
def run_event_sender(event_result):

    pass


@app.task
def get_task_state():

    return



@app.task(bind=True)
def run_module(self):
    # Load saved settings
    settings_path = os.path.join(os.getcwd(), "config", "settings.yml")
    settings = load_settings(settings_path)["settings"]

    # Parse setting options
    cctv_info = settings["cctv_info"]
    streaming_url = cctv_info["streaming_url"]
    streaming_type = cctv_info["streaming_type"]
    decode_option = settings["decode_option"]
    extract_fps = int(decode_option["fps"])
    fps = 0

    model_info = settings["model"]
    object_model_info = model_info["object_detection"]
    object_model_name = object_model_info["model_name"]
    object_score_threshold = float(object_model_info["score_threshold"])
    object_nms_threshold = float(object_model_info["nms_threshold"])
    event_model_info = model_info["event"]
    event_model_names = event_model_info["event_names"]

    # Load edge module manager
    module_manager = EdgeModuleManager()
    ret = module_manager.load_decoder(streaming_url, extract_fps)
    if ret:
        message = "Edge module manager is successfully loaded."
        logger.info(message)
        self.update_state(state="PROGRESS", meta={"message": message})
    else:
        message = "Edge module manager loading is failed"
        self.update_state(state="FAILED", meta={"message": message})
        logger.info(message)
        return

    # Load object detection model
    self.update_state(state="PROGRESS", meta={"message": "Start model loading".format(object_model_name)})

    ret = module_manager.load_object_model(object_model_name, object_score_threshold, object_nms_threshold)
    if ret:
        message = "Object detection model({}) is successfully loaded.".format(object_model_name)
        logger.info(message)
        self.update_state(state="PROGRESS", meta={"message": message})
    else:
        message = "Object detection model loading is failed.({})".format(object_model_name)
        self.update_state(state="FAILED", meta={"message": message})
        logger.info(message)
        return

    # Load event detection models
    ret = module_manager.load_event_model(event_model_names)
    if ret:
        message = "Event detection model({}) is successfully loaded.".format(", ".join(event_model_names))
        logger.info(message)
        self.update_state(state="PROGRESS", meta={"message": message})
    else:
        message = "Event detection model loading is failed."
        self.update_state(state="FAILED", meta={"message": message})
        logger.info(message)
        return

    fps = module_manager.fps
    decoder_thread = threading.Thread(target=module_manager.run_decoder,)
    decoder_thread.start()
    self.update_state(state="PROGRESS", meta={"message": "Decoder started"})

    frame_number = 0
    self.update_state(state="PROGRESS", meta={"message": "Event detection started"})
    while True:
        if len(module_manager.frame_buffer) > 0:
            frame = module_manager.frame_buffer.pop(0)
            frame_info = {"frame": frame, "frame_number": int(frame_number / extract_fps * fps)}
            object_results = module_manager.object_model.inference_by_image(frame)
            reformat_result = reformat_object_result(object_model_name, frame_number, fps, extract_fps, object_results)

            for event_model in module_manager.event_models:
                event_model.inference(frame_info, reformat_result)
                event_model.merge_sequence(frame_info, 0)

            for event_model in module_manager.event_models:
                now = datetime.datetime.now()
                if event_model.new_seq_flag == True and frame_number > extract_fps: # 모듈 시작 직후 message 보내는 부분 방지
                    event_model.new_seq_flag = False
                    # communicator.send_event(event_model.model_name, now, "start", None)
                    logger.info("Send start time of {} event sequence({}) - frame number: {}".format(event_model.model_name, now, frame_number))
                if len(event_model.frameseq) > 0:
                    sequence = event_model.frameseq.pop()
                    message = sequence
                    message["duration"] = (sequence["end_frame"] - sequence["start_frame"]) / module_manager.fps
                    # communicator.send_event(event_model.model_name, now, "end", message)
                    logger.info("Send end time of {} event sequence({}) - frame number: {}".format(event_model.model_name, now, frame_number))

            frame_number += 1
        else:
            if not module_manager.decoder.capture.isOpened():
                self.update_state(state="FINISHED", meta={"message": "CCTV streaming is closed."})
                break
