import argparse
import json
import os
import cv2
import time
from detector.object_detection.yolov4 import YOLOv4
import pycuda.autoinit

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--video_path", type=str, default="videos/1_360p.mp4", help="Video path")
    parser.add_argument("--fps", type=int, default=7, help="FPS of extraction frame ")
    parser.add_argument("--model_name", type=str, default="yolov4-416", help="Model name")
    parser.add_argument("--score_threshold", type=float, default=0.5, help="Model name")
    parser.add_argument("--nms_threshold", type=float, default=0.3, help="Model name")
    parser.add_argument("--result_dir", type=str, default="./", help="Ground truth file(json)")

    opt = parser.parse_known_args()[0]

    video_path = opt.video_path
    video_name = video_path.split("/")[-1]
    fps = opt.fps
    score_threshold = opt.score_threshold
    nms_threshold = opt.nms_threshold
    model_name = opt.model_name
    result_dir = opt.result_dir
    frame_dir = os.path.join(result_dir, video_name.split(".mp4")[0])
    json_dir = os.path.join(result_dir, video_name.split(".mp4")[0])

    model = YOLOv4(score_threshold=score_threshold, nms_threshold=nms_threshold)
    capture = cv2.VideoCapture(video_path)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if not os.path.exists(frame_dir):
        os.makedirs(frame_dir)
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    frame_number = 0
    while True:
        ret, frame = capture.read()

        if ret:
            if frame_number % fps == 0:
                frame_name = "{0:06d}".format(frame_number + 1)
                cv2.imwrite(os.path.join(frame_dir, frame_name + ".jpg"), frame)

                start_time = time.time()
                results = model.inference_by_image(frame)
                end_time = time.time()

                dict_result = dict()
                dict_result["image_path"] = "./data/frames/1_360p/" + frame_name + ".jpg"
                dict_result["module"] = model_name
                dict_result["cam_id"] = 0
                dict_result["analysis_time"] = end_time - start_time
                dict_result["frame_number"] = frame_number
                dict_result["results"] = results

                json_result_file = open(os.path.join(json_dir, frame_name + ".json"), "w")
                json.dump(dict_result,json_result_file, indent=4)
                json_result_file.close()

                print("\rframe number: {:>6}/{}".format(frame_number, frame_count), end='')

            frame_number += 1
        else:
            print()
            break