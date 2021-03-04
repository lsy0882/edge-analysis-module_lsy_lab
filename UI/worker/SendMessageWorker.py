from datetime import timedelta
from PyQt5.QtCore import QThread, pyqtSignal
import time


class SendMessageWorker(QThread):
    edit_text_log_signal = pyqtSignal(str)

    def __init__(self, video_worker, parent=None):
        super().__init__()
        self.video_worker = video_worker
        self.result_queue = []
        self.run_send_message = False
        self.pause = False
        self.is_started = False

    def __del__(self):
        del self

    def run(self):
        self.run_send_message = True
        self.is_started = True
        send_result_message_count = 0

        is_ended = False
        while self.run_send_message:
            if not self.video_worker.run_video:
                if is_ended == False:
                    self.edit_text_log_signal.emit("VERBOSE:\tAnalysis End - ({})".format(str(timedelta(seconds=self.video_worker.running_time))))
                    is_ended = True

            if not self.pause :
                if len(self.result_queue) > 0:
                    print(self.result_queue.pop(0))
                send_result_message_count += 1
                time.sleep(0.2)
            else :
                time.sleep(1)

    def pause_worker(self):
        self.pause = True

    def resume_worker(self):
        self.pause = False

    def get_start_state(self):
        return self.is_started