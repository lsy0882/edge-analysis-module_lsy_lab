import cv2
import threading

class CvDecoder(object):
    def __init__(self, url, fps, cam_id, is_show=False):
        self.url = url
        self.fps = fps
        self.cam_id = cam_id
        self.window_name = "cam_" + str(cam_id)
        self.is_show = is_show
        self.frame_num = 0
        self.frame_queue = []

    def init_capture(self):
        try:
            self.capture = cv2.VideoCapture(self.url)
            return True
        except:
            print("Error: Fail to open url {}".format(self.url))
            return False

    def decode_video(self):
        if self.is_show :
            cv2.namedWindow(self.window_name)

        while True:
            ret, frame = self.capture.read()
            self.frame_num += 1

            if self.frame_num % self.fps == 1:
                self.frame_queue.append({"frame_num": self.frame_num, "frame": frame})

            if ret == False:
                break


    def show_frame(self, frame):
        cv2.imshow(self.window_name, frame)

class DecoderThread(threading.Thread) :
    def __init__(self, url, fps, cam_id, is_show=False):
        threading.Thread.__init__(self)
        self.url = url
        self.cam_id = cam_id
        self.decoder = CvDecoder(url, fps, cam_id, is_show=is_show)
        self.decoder.init_capture()

    def run(self):
        print("INFO: Start Decoding")
        self.decoder.decode_video()

    def getFrameFromFQ(self):
        if len(self.decoder.frame_queue) > 0:
            frame_info = self.decoder.frame_queue.pop()
            return frame_info
        else:
            return None


