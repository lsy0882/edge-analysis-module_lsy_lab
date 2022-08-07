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

    # Load edge module manager
    try:
        module_manager = EdgeModuleManager(settings, logger, self)
        module_manager.load_decoder()
        module_manager.load_models()
        message = "Edge module manager is successfully loaded."
        logger.info(message)
        self.update_state(state="PROGRESS", meta={"message": message})
    except:
        message = "Edge module manager loading is failed"
        self.update_state(state="FAILED", meta={"message": message})
        logger.info(message)
        return
    # Start to run module
    try:
        module_manager.run()
    except:
        message = "Error occurred while executing the module."
        self.update_state(state="FAILED", meta={"message": message})
        logger.info(message)

    self.update_state(state="END", meta={"message": "End module"})