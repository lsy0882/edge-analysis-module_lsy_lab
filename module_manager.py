from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

from decoder.CvDecoder import CvDecoder
from detector.object_detection.yolov4.yolov4 import YOLOv4
from detector.event.assault.main import AssaultEvent
from detector.event.falldown.main import FalldownEvent
from detector.event.kidnapping.main import KidnappingEvent
from detector.event.tailing.main import TailingEvent
from detector.event.wanderer.main import WandererEvent


class EdgeModuleManager:
    object_model_class = {
        "yolov4-416": YOLOv4
    }
    event_model_class = {
        "assault": AssaultEvent,
        "falldown": FalldownEvent,
        "kidnapping": KidnappingEvent,
        "tailing": TailingEvent,
        "wanderer": WandererEvent,
    }

    def __init__(self):
        self.frame_buffer = []
        self.streaming_url = ""
        self.streaming_type = "cctv"
        self.fps = 0
        self.extract_fps = 0
        self.decoder_thread = None
        self.filter_frame_numbers = []
        self.object_model = None
        self.event_models = []

    def load_decoder(self, streaming_url, extract_fps):
        self.streaming_url = streaming_url
        self.extract_fps = extract_fps
        self.decoder = CvDecoder(self.streaming_url)
        ret = self.decoder.load()
        if ret:
            logger.info("Streaming url is successfully loaded.")
            self.fps = self.decoder.fps
            ret = self.__generate_filter_numbers(self.extract_fps, self.fps)
            if not ret:
                return False
            return True
        else:
            logger.info("Streaming url loading is failed.")
            return False

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

    def __generate_filter_numbers(self, extract_fps, fps):
        if extract_fps is not 0 and fps is not 0:
            tmp_nums = []
            for i in range(1, fps + 1):
                filter_num = int(i * (extract_fps / fps))
                if filter_num != 0 and filter_num not in tmp_nums:
                    tmp_nums.append(filter_num)
                    self.filter_frame_numbers.append(i)
            logger.info("Extract frame number is {}".format(str(self.filter_frame_numbers).replace("[", "").replace("]", "")))
            return True
        else:
            logger.info("There is wrong fps or extract fps(fps: {} / extract fps {})".format(fps, extract_fps))
            return False

    def load_object_model(self, object_model_name, object_score_threshold, object_nms_threshold):
        try:
            import pycuda.autoinit

            self.object_model = self.object_model_class[object_model_name](
                model=object_model_name,
                score_threshold=object_score_threshold,
                nms_threshold=object_nms_threshold
            )
            logger.info("{} model is loaded".format("Object detection(yolov4)"))
            return True
        except:
            return False

    def load_event_model(self, model_names):
        for event_model_name in self.event_model_class.keys():
            try:
                if event_model_name in model_names:
                    event_model = self.event_model_class[event_model_name](debug=True)
                    self.event_models.append(event_model)
                    logger.info("{} model is loaded".format(event_model.model_name))
            except:
                logger.info("Cannot load \"{}\" event detection model.".format(event_model_name))

        if len(self.event_models) != len(model_names):
            return False
        else:
            return True

    def load_tracker(self, tracker_names):
        pass