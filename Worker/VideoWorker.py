import cv2
from PyQt5 import QtCore, QtGui
from datetime import datetime

from utils.yolo_classes import get_cls_dict
from utils.Visualize import BBoxVisualization

class VideoWorker(QtCore.QObject):
    video_signal_frame = QtCore.pyqtSignal(QtGui.QImage)

    def __init__(self, parent=None, width=640, height=360):
        super(VideoWorker, self).__init__(parent)
        self.run_video = True
        self.frame = None
        self.analysis_fps = 0
        self.height = height
        self.width = width
        self.detection_result = None
        self.cls_dict = dict()
        self.video_type = ""
        self.bbox_visualization = None
        self.frame_queue = []
        self.object_detection_result_queue = []
        self.running_time = 0

        self.video_url = ""
        self.video_fps = 0.0
        self.display_delay = 0
        self.server_url = ""
        self.server_port = ""
        self.dataset_index = 0
        self.capture = None

    def set_attribute(self, settings_attr):
        self.video_url = settings_attr["video_url"]
        self.analysis_fps = float(settings_attr["analysis_fps"])
        self.display_delay = int(settings_attr["display_delay"])
        self.server_url = settings_attr["server_url"]
        self.server_port = settings_attr["server_port"]
        self.dataset_index = settings_attr["dataset"]

        self.capture = cv2.VideoCapture(settings_attr["video_url"])
        self.video_fps = float(self.capture.get(cv2.CAP_PROP_FPS))

        if "://" in self.video_url:
            self.video_type = "streaming"
        else:
            self.video_type = "file"

        if self.dataset_index == 0:   # obstacle
            self.cls_dict = get_cls_dict(15)
        elif self.dataset_index == 1: # mscoco
            self.cls_dict = get_cls_dict(80)

        self.bbox_visualization = BBoxVisualization(self.cls_dict)

    def get_video_worker_info(self):
        log = "VERBOSE:\tVideo info\n"
        if self.video_type == "streaming":
            log += "\tVideo URL\t: {}\n".format(self.video_url)
        else :
            log += "\tVideo Path\t: {}\n".format(self.video_url)
        log += "\tResolution\t: {}x{}\n".format(self.width, self.height)
        log += "\tVideo fps\t: {}\n".format(self.video_fps)
        log += "\tAnalysis fps\t: {}\n".format(self.analysis_fps)
        log += "\tDisplay delay: {}\n".format(self.display_delay)
        log += "\tServer URL\t: {}:{}\n".format(self.server_url, self.server_port)
        return log


    @QtCore.pyqtSlot()
    def event_start(self):
        self.run_video = True
        frame_number = 0
        import time
        start = time.time()
        while True:
            ret, self.frame = self.capture.read()

            if not ret :
                break
            else :
                if frame_number % (self.analysis_fps * 30) == 0:
                    self.frame_queue.append([frame_number, self.frame])

                if len(self.object_detection_result_queue) > 0:
                    if len(self.object_detection_result_queue) > 1:
                        self.object_detection_result_queue.pop(0)
                    self.bbox_visualization.draw_bboxes(self.frame, self.object_detection_result_queue[0])

                if frame_number % self.display_delay == 0:
                    color_swapped_image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

                    qt_image = QtGui.QImage(color_swapped_image.data,
                                            self.width,
                                            self.height,
                                            color_swapped_image.strides[0],
                                            QtGui.QImage.Format_RGB888)
                    self.video_signal_frame.emit(qt_image)

                    loop = QtCore.QEventLoop()
                    QtCore.QTimer.singleShot(self.display_delay, loop.quit)  # 25 ms
                    loop.exec_()

            frame_number += 1
        end = time.time()
        self.running_time = end - start
        self.run_video = False

    def event_stop(self):
        self.run_video = False
