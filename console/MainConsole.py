import threading

from module.EventManager import EventManager
from utils import PrintLog
from communicator.Socket import Communicator
from decoder.DecoderManagerConsole import DecoderManager
from detector.yolov4 import YOLOv4


class MainConsole:

    def __init__(self, cam_address, server_address, analysis_fps, object_detection_model, object_detection_dataset):
        self.cam_address = cam_address
        self.server_address = server_address
        self.analysis_fps = analysis_fps

        self.frame_info_pool = []
        self.object_detection_result_pool = []
        self.final_result_pool = []

        self.communicator = None
        self.communicator_thread = None

        self.decoder_manager = None
        self.decoder_thread = None

        self.object_detector = None
        self.object_detection_model = object_detection_model
        self.object_detection_dataset = object_detection_dataset
        self.object_detector_thread = None

        self.event_manager = None
        self.event_manager_thread = None

    def init(self):
        # Load Communicator
        if self.server_address != "":
            try:
                self.communicator = Communicator()
                print(self.cam_address, self.cam_address)
                self.communicator.load_client(self.server_address, self.cam_address, self.final_result_pool)
                self.communicator_thread = threading.Thread(target=self.communicator.run)
            except:
                return False, PrintLog.e("Socket communicator failed to load.")

        # Load Object Detector
        try:
            self.object_detector = YOLOv4(self.frame_info_pool, self.object_detection_result_pool, self.final_result_pool,model=self.object_detection_model, dataset=self.object_detection_dataset, )
        except:
            return False, PrintLog.e("Object detector failed to load.")

        # Load Event Detector
        try:
            self.event_manager = EventManager(self.object_detection_result_pool, self.final_result_pool)
            self.event_manager_thread = threading.Thread(target=self.event_manager.run)
        except:
            return False, PrintLog.e("Object detector failed to load.")

        # Load Decoder Manager
        try:
            self.decoder_manager = DecoderManager(self.analysis_fps, self.cam_address, self.frame_info_pool)
            self.decoder_thread = threading.Thread(target=self.decoder_manager.run)
        except:
            return False, PrintLog.e("Decoder manager failed to load.")

        PrintLog.i("Edge analysis module is successfully loaded.")
        return True

    def run(self):
        if self.communicator_thread is not None:
            self.communicator_thread.start()
        self.decoder_thread.start()
        self.event_manager_thread.start()

        self.object_detector.run()
