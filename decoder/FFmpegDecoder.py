from decoder.Decoder import Decoder
import numpy
import subprocess

class FFmpegDecoder(Decoder):
    def __init__(self, video_url, width=640, height=360, fps=20):
        super().__init__(video_url)
        self.width = width
        self.height = height
        self.fps = fps
        self.pipe = None

    def load(self):
        self.command = ['ffmpeg',
                        '-y', '-hide_banner', '-loglevel', 'panic',
                        '-i', self.video_url,
                        '-pix_fmt', 'bgr24',
                        '-r', str(self.fps),
                        '-vcodec', 'rawvideo',
                        '-f', 'image2pipe',
                        'pipe:1']
        self.pipe = subprocess.Popen(self.command, stdout=subprocess.PIPE, bufsize=self.width * self.height * 3)

    def read(self):
        try :
            raw_image = self.pipe.stdout.read(self.width * self.height * 3)
            self.pipe.stdout.flush()

            uint8_image = numpy.frombuffer(raw_image, dtype='uint8')
            if uint8_image.shape[0] == 0:
                return False, None
            else:
                frame = uint8_image.reshape((self.height, self.width, 3))
                return True, frame
        except:
            return False, None

    def release(self):
        del self.pipe



