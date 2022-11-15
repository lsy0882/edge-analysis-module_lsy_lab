from module_manager import EdgeModuleManager
from utils.params_util import *

import os
from celery import Celery
from celery.result import AsyncResult
from celery.utils.log import get_task_logger

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

app = Celery('tasks', broker=BROKER_URL, backend=CELERY_RESULT_BACKEND)
logger = get_task_logger(__name__)


@app.task
def run_event_sender(event_result):

    pass


def get_task_state(task_id, task_state):
    result = AsyncResult(task_id, app=app)
    if task_state == result.state:
        return True
    else:
        return False


def del_task(task_id):
    try:
        app.control.revoke(task_id, terminate=True, signal='SIGKILL')
        return True
    except:
        return False


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
        message = "Analysis task is successfully started"
        self.update_state(state="PROGRESS", meta={"message": message})
        module_manager.run()
    except:
        message = "Error occurred while executing the module."
        self.update_state(state="FAILED", meta={"message": message})
        logger.info(message)

    self.update_state(state="END", meta={"message": "End module"})
