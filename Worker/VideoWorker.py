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

        self.height = height
        self.width = width
        self.detection_result = None
        self.video_fps = 0.0
        self.analysis_fps = 0
        self.cls_dict = dict()
        self.video_type = ""
        self.vis = None
        self.frame_queue = []
        self.object_detection_result_queue = []
        self.running_time = 0

    def set_attribute(self, video_url, extract_fps, class_num=15, display_fps=1):
        self.video_url = video_url
        self.capture = cv2.VideoCapture(video_url)
        if "://" in video_url:
            self.video_type = "streaming"
        else:
            self.video_type = "file"
        self.video_fps = float(self.capture.get(cv2.CAP_PROP_FPS))
        self.analysis_fps = int(extract_fps)
        self.cls_dict = get_cls_dict(class_num)
        self.vis = BBoxVisualization(self.cls_dict)
        self.display_fps = display_fps

    def get_video_worker_info(self):
        log = "VERBOSE:\tVideo info\n"
        if self.video_type == "streaming":
            log += "\tVideo URL\t: {}\n".format(self.video_url)
        else :
            log += "\tVideo path\t: {}\n".format(self.video_url)
        log += "\tResolution\t: {}x{}\n".format(self.width, self.height)
        log += "\tVideo fps\t: {}\n".format(self.video_fps)
        log += "\tAnalysis fps: {}".format(self.analysis_fps)
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
                    self.vis.draw_bboxes(self.frame, self.object_detection_result_queue[0])

                if frame_number % self.display_fps == 0:
                    color_swapped_image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

                    qt_image = QtGui.QImage(color_swapped_image.data,
                                            self.width,
                                            self.height,
                                            color_swapped_image.strides[0],
                                            QtGui.QImage.Format_RGB888)
                    self.video_signal_frame.emit(qt_image)

                    loop = QtCore.QEventLoop()
                    QtCore.QTimer.singleShot(1, loop.quit)  # 25 ms
                    loop.exec_()

            frame_number += 1
        end = time.time()
        self.running_time = end - start
        self.run_video = False

    def event_stop(self):
        self.run_video = False

    def get_timestamp(self, frame_number, fps):
        if self.video_type == "streaming":
            return datetime.now().strftime("%Y/%d/%m %H:%M:%S")
