import argparse
import json
import os
from Decoder.CvDecoder import DecoderThread
from Detection.EventsDetector import EventDetector
from Detection.ObjectDetector import JIDetector

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--video", type=str, required=True, help="Video path")
    parser.add_argument("--event_dir", type=str, required=True, help="Event json dir")
    parser.add_argument("--fps", type=int, default=6, help="FPS of extraction frame ")
    parser.add_argument("--model_name", type=str, default="ssd-mobilenet-v2", help="Model name")
    parser.add_argument("--debug", type=bool, default=False, help="Debug")
    parser.add_argument("--display", type=bool, default=False, help="Display")
    parser.add_argument("--show_scale", type=int, default=1, help="Show scale")
    parser.add_argument("--metadata", type=str, default="", help="Ground truth file(json)")

    opt = parser.parse_known_args()[0]

    video_path = opt.video
    event_json_dir = opt.event_dir

    decoder_thread = DecoderThread(video_path, opt.fps, 0, False)
    decoder_thread.start()

    object_detector = JIDetector(opt.model_name)
    event_detector = EventDetector()

    count = 0

    while True :
        try :
            frame_info = decoder_thread.getFrameFromFQ()
            od_result = object_detector.detect(frame_info)
            event_result = event_detector.detect_event(od_result)

            print("\rframe_num: {}\t/ json_count: {}".format(frame_info["frame_num"], count), end='')
            count+=1
            with open(os.path.join(event_json_dir, "%06d.json"%(count)), "w") as json_file:
                json.dump(event_result, json_file, indent="\t")
                json_file.close()

        except:
            pass