import argparse
import json
import os
import cv2
import time
from detector.object_detection.yolov4 import YOLOv4
import pycuda.autoinit

from utils import PrintLog

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--video_path", type=str, default="videos/1_360p.mp4", help="Video path")
    parser.add_argument("--fps", type=int, default=30, help="FPS of extraction frame ")
    parser.add_argument("--model_name", type=str, default="yolov4-416", help="Model name")
    parser.add_argument("--score_threshold", type=float, default=0.5, help="Model name")
    parser.add_argument("--nms_threshold", type=float, default=0.3, help="Model name")
    parser.add_argument("--result_dir", type=str, default="./", help="Ground truth file(json)")

    opt = parser.parse_known_args()[0]

    video_path = opt.video_path
    video_name = video_path.split("/")[-1]
    extract_fps = opt.fps
    score_threshold = opt.score_threshold
    nms_threshold = opt.nms_threshold
    model_name = opt.model_name
    result_dir = opt.result_dir
    frame_dir = os.path.join(result_dir, video_name.split(".mp4")[0])
    json_dir = os.path.join(result_dir, video_name.split(".mp4")[0])

    model = YOLOv4(score_threshold=score_threshold, nms_threshold=nms_threshold)
    capture = cv2.VideoCapture(video_path)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(round(capture.get(cv2.CAP_PROP_FPS)))

    PrintLog.i("YOLO detector information\n"
               "\tmodel name: {}\n"
               "\tscore threshold: {}\n"
               "\tnms threshold: {}"
               .format(model_name, score_threshold, nms_threshold))

    PrintLog.i("Extract information\n"
               "\tvideo path: {}\n"
               "\tvideo fps: {}\n"
               "\tvideo framecount: {}\n"
               "\textract fps: {}\n"
               "\textract frame number: {}"
               .format(video_path, fps, frame_count, extract_fps, int(frame_count/(fps/extract_fps))))

    if not os.path.exists(frame_dir):
        os.makedirs(frame_dir)
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    frame_number = 1

    frame_path_list = list()
    try:
        command = "ffmpeg -y -hide_banner -loglevel panic -i {} -vsync 2 -q:v 0 -vf fps={} {}/%04d.jpg".format(video_path, extract_fps, os.path.join(frame_dir))
        os.system(command)
        frame_path_list = os.listdir(frame_dir)
        PrintLog.i("Frame extraction is successfully completed(path: {}, framecount: {})".format(frame_dir, len(frame_path_list)))
    except:
        PrintLog.e("Frame extraction is failed")
        exit(0)

    for i, frame_name in enumerate(frame_path_list):
        frame = cv2.imread(os.path.join(frame_dir, frame_name))

        start_time = time.time()
        results = model.inference_by_image(frame)
        end_time = time.time()

        dict_result = dict()
        dict_result["image_path"] = os.path.join(frame_dir, frame_name)
        dict_result["module"] = model_name
        dict_result["cam_id"] = 0
        dict_result["analysis_time"] = end_time - start_time
        dict_result["frame_number"] = frame_number
        dict_result["results"] = results

        json_result_file = open(os.path.join(json_dir, frame_name.split(".jpg")[0] + ".json"), "w")
        json.dump(dict_result,json_result_file, indent=4)
        json_result_file.close()

        print("\rframe number: {:>6}/{}".format(frame_number, len(frame_path_list)), end='')
        frame_number += 1

    print()
    PrintLog.i("Extraction is successfully completed(framecount: {})".format(frame_number))