from decoder.Decoder import Decoder
import numpy
import cv2


class CvDecoder(Decoder):
    def __init__(self, streaming_url, width=640, height=360, fps=20):
        super().__init__(streaming_url)
        self.streaming_url = streaming_url
        self.width = width
        self.height = height
        self.fps = fps
        self.capture = None

    def load(self):
        self.capture = cv2.VideoCapture(self.streaming_url)
        if self.capture.isOpened():
            self.fps = int(round(self.capture.get(cv2.CAP_PROP_FPS)))
            return True
        else:
            return False

    def read(self):
        try:
            ret, frame = self.capture.read()
            return ret, frame
        except:
            return False, None

    def release(self):
        self.capture.release()
