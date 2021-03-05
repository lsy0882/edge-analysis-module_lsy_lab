from decoder.CvDecoder import CvSingleDecoder, CvMultipleDecoder
from utils import PrintLog

class DecoderManager:
    def __init__(self, analysis_fps, cam_address, frame_info_pool):
        self.cam_address = self.address_spliter(cam_address)
        self.frame_info_pool = frame_info_pool
        self.analysis_fps = analysis_fps
        self.decoder = None
        PrintLog.i("Decoder loading is started")
        if len(self.cam_address) == 1:
            self.decoder = CvSingleDecoder(self.cam_address[0], analysis_fps)
        else :
            self.decoder = CvMultipleDecoder(self.cam_address, analysis_fps)
        PrintLog.i("Decoder is loaded - {}".format(cam_address))

    def run(self):
        while True:
            frame_infos = self.decoder.read()
            if type(frame_infos) == list:
                for frame_info in frame_infos:
                    if frame_info["frame"] is not None:
                        self.frame_info_pool.append(frame_info)
            else:
                if frame_infos is not None and frame_infos["frame"] is not None:
                    self.frame_info_pool.append(frame_infos)

    def address_spliter(self, cam_address):
        return cam_address.split(",")