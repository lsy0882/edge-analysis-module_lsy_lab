import cv2
import time
from decoder.Decoder import Decoder
from utils import PrintLog


class CvSingleDecoder(Decoder):
    def __init__(self, cam_address, analysis_fps):
        super().__init__(cam_address)
        self.ret = None
        self.frame = None
        self.frame_number = 0
        self.cam_address = cam_address
        self.video_capture = cv2.VideoCapture(self.cam_address)
        self.fps = 0
        if not self.video_capture.isOpened():
            self.video_capture = None
            PrintLog.e("Invalid URL({})".format(self.cam_address))
        else:
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.analysis_fps = int(self.fps / analysis_fps)

    def read(self):
        super().read()

        if self.video_capture is not None:
            self.ret, self.frame = self.video_capture.read()
            if self.ret:
                self.frame_number += 1
                if self.frame_number % self.analysis_fps == 0:
                    return {"cam_address": self.cam_address, "frame": self.frame, "frame_number": self.frame_number, "timestamp": float(time.time())}
                else:
                    return None

class CvMultipleDecoder:
    def __init__(self, cam_addresss, analysis_fps=4):
        self.cam_addresses = cam_addresss
        self.decoders = []

        for cam_address in self.cam_addresses:
            self.decoders.append(CvSingleDecoder(cam_address, analysis_fps))

    def read(self):
        frame_infos = []
        for i, decoder in enumerate(self.decoders):
            frame_info = decoder.read()
            if frame_info is not None:
                frame_infos.append(frame_info)

        return frame_infos
