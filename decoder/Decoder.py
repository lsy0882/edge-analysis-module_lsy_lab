class Decoder:
    def __init__(self, video_url, buffer_size=30):
        self.video_url = video_url
        self.framebuffer = None
        self.buffer_size = buffer_size

    def read(self):
        pass

    def __delete__(self, instance):
        pass