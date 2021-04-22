import argparse
import json
import os
import cv2
import csv

import pycuda.autoinit

from detector.event.assault.main import AssaultEvent
from detector.event.falldown.main import FalldownEvent
from detector.event.kidnapping.main import KidnappingEvent
from detector.event.obstacle.main import ObstacleEvent
from detector.event.tailing.main import TailingEvent
from detector.event.wanderer.main import WandererEvent
from detector.object_detection.yolov4 import YOLOv4

from utils.time_util import convert_framenumber2timestamp
from utils import PrintLog
from utils.yolo_classes import get_cls_dict
from utils.Visualize import BBoxVisualization


def split_model_names(model_names):
    return model_names.split(",")

def load_video(video_path):
    capture = cv2.VideoCapture(video_path)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(round(capture.get(cv2.CAP_PROP_FPS)))

    PrintLog.i("Extract information\n"
               "\tvideo path: {}\n"
               "\tvideo fps: {}\n"
               "\tvideo framecount: {}\n"
               "\textract fps: {}\n"
               "\textract frame number: {}"
               .format(video_path, fps, frame_count, extract_fps, int(frame_count/(fps/extract_fps))))
    return capture, frame_count, fps


def load_models(od_model_name, score_threshold, nms_threshold, event_model_names):
    od_model = YOLOv4(model=od_model_name, score_threshold=score_threshold, nms_threshold=nms_threshold)

    PrintLog.i("YOLO detector information\n"
               "\tmodel name: {}\n"
               "\tscore threshold: {}\n"
               "\tnms threshold: {}"
               .format(od_model_name, score_threshold, nms_threshold))

    event_detectors = []
    PrintLog.i("{} model is loaded".format("Object detection(yolov4)"))

    splited_model_names = split_model_names(event_model_names)

    if event_model_names == "all" or "assault" in splited_model_names:
        assault_detection_model = AssaultEvent()
        event_detectors.append(assault_detection_model)
        PrintLog.i("{} model is loaded".format(assault_detection_model.model_name))

    if event_model_names == "all" or "falldown" in splited_model_names:
        falldown_detection_model = FalldownEvent()
        event_detectors.append(falldown_detection_model)
        PrintLog.i("{} model is loaded".format(falldown_detection_model.model_name))

    if event_model_names == "all" or "obstacle" in splited_model_names:
        obstacle_detection_model = ObstacleEvent()
        event_detectors.append(obstacle_detection_model)
        PrintLog.i("{} model is loaded".format(obstacle_detection_model.model_name))

    if event_model_names == "all" or "kidnapping" in splited_model_names:
        kidnapping_detection_model = KidnappingEvent()
        event_detectors.append(kidnapping_detection_model)
        PrintLog.i("{} model is loaded".format(kidnapping_detection_model.model_name))

    if event_model_names == "all" or "tailing" in splited_model_names:
        tailing_detection_model = TailingEvent()
        event_detectors.append(tailing_detection_model)
        PrintLog.i("{} model is loaded".format(tailing_detection_model.model_name))

    if event_model_names == "all" or "wanderer" in splited_model_names:
        wanderer_detection_model = WandererEvent()
        event_detectors.append(wanderer_detection_model)
        PrintLog.i("{} model is loaded".format(wanderer_detection_model.model_name))

    return od_model, event_detectors


def make_result_dir(result_dir, video_name):
    frame_dir = os.path.join(result_dir, video_name.split(".mp4")[0], "frame")
    fram_bbox_dir = os.path.join(result_dir, video_name.split(".mp4")[0], "fram_bbox")
    json_dir = os.path.join(result_dir, video_name.split(".mp4")[0], "json")
    event_dir = os.path.join(result_dir, video_name.split(".mp4")[0])

    if not os.path.exists(frame_dir):
        os.makedirs(frame_dir)
    if not os.path.exists(fram_bbox_dir):
        os.makedirs(fram_bbox_dir)
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    return frame_dir, fram_bbox_dir, json_dir, event_dir


def run_ffmpeg(video_path, extract_fps, frame_dir):
    try:
        command = "ffmpeg -y -hide_banner -loglevel panic -i {} -vsync 2 -q:v 0 -vf fps={} {}/%04d.jpg".format(video_path, extract_fps, frame_dir)
        os.system(command)
        frame_path_list = os.listdir(frame_dir)
        PrintLog.i("Frame extraction is successfully completed(path: {}, framecount: {})".format(frame_dir, len(frame_path_list)))
        return frame_path_list
    except:
        PrintLog.e("Frame extraction is failed")
        exit(0)


def run_detection(od_model, event_detectors, frame_path_list, fram_bbox_dir):
    frame_number = 0
    event_results = []
    cls_dict = get_cls_dict(15)
    bbox_visualization = BBoxVisualization(cls_dict)
    for i, frame_name in enumerate(frame_path_list):
        frame_number += 1
        frame = cv2.imread(os.path.join(frame_dir, frame_name))

        results = od_model.inference_by_image(frame)

        frame_bbox = bbox_visualization.draw_bboxes(frame, results)
        cv2.imwrite(os.path.join(fram_bbox_dir, frame_name), frame_bbox)

        dict_result = dict()
        dict_result["image_path"] = os.path.join(frame_dir, frame_name)
        dict_result["cam_address"] = video_path
        dict_result["module"] = od_model_name
        dict_result["frame_number"] = int(frame_number / extract_fps * fps)
        dict_result["timestamp"] = str(convert_framenumber2timestamp(frame_number, fps))
        dict_result["results"] = []
        dict_result["results"].append({"detection_result": results})

        event_result = dict()
        event_result["cam_address"] = video_path
        event_result["frame_number"] = int(frame_number / extract_fps * fps)
        event_result["timestamp"] = str(convert_framenumber2timestamp(frame_number, fps))
        event_result["event_result"] = dict()

        for event_detector in event_detectors:
            event_result["event_result"][event_detector.model_name] = event_detector.inference(dict_result)

        event_results.append(event_result)
        print("\rframe number: {:>6}/{}\t/ extract frame number: {:>6}\t/ timestamp: {:>6}"
              .format(frame_number, len(frame_path_list), int(frame_number / extract_fps * fps), str(convert_framenumber2timestamp(frame_number / extract_fps * fps, fps))), end='')

        json_result_file = open(os.path.join(json_dir, frame_name.split(".jpg")[0] + ".json"), "w")
        json.dump(dict_result, json_result_file, indent=4)
        json_result_file.close()


    PrintLog.i("\nExtraction is successfully completed(framecount: {})".format(frame_number))

    return event_results


def extract_event_results(event_dir, video_name, event_detectors, event_results):
    event_csv_file_path = os.path.join(event_dir, video_name.split(".mp4")[0] + ".csv")
    with open(event_csv_file_path, "w") as event_file:
        csv_writer = csv.writer(event_file)
        event_names = []
        name = [""]
        for i, event_detector in enumerate(event_detectors):
            name.append(event_detector.model_name)
            event_names.append(event_detector.model_name)

        csv_writer.writerow(name)

        for event_result in event_results:
            row = ["{:>10}".format(event_result["frame_number"])]
            for i, event_name in enumerate(event_names):
                if event_result["event_result"][event_name]:
                    row.append(i+1)
                else:
                    row.append("")
            csv_writer.writerow(row)
    PrintLog.i("Event result file is successfully extracted.(path: {})".format(event_csv_file_path))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--video_path", type=str, default="videos/1_360p.mp4", help="Video path")
    parser.add_argument("--fps", type=int, default=22, help="FPS of extraction frame ")
    parser.add_argument("--od_model_name", type=str, default="yolov4-416", help="Object detection model name")
    parser.add_argument("--score_threshold", type=float, default=0.5, help="Object detection score threshold")
    parser.add_argument("--nms_threshold", type=float, default=0.3, help="Object detection nms threshold")
    parser.add_argument("--event_model", type=str, default="all", help="Event model names")
    parser.add_argument("--result_dir", type=str, default="./result", help="Directory path of results and frame")

    option = parser.parse_known_args()[0]

    video_path = option.video_path
    video_name = video_path.split("/")[-1]
    extract_fps = option.fps
    score_threshold = option.score_threshold
    nms_threshold = option.nms_threshold
    od_model_name = option.od_model_name
    event_model_names = option.event_model
    result_dir = option.result_dir

    # Load Video
    capture, frame_count, fps = load_video(video_path)

    # Load Object Detection & Event Detection models
    od_model, event_detectors = load_models(od_model_name, score_threshold=score_threshold, nms_threshold=nms_threshold, event_model_names=event_model_names)

    # Result Directory info
    frame_dir, fram_bbox_dir, json_dir, event_dir = make_result_dir(result_dir, video_name)

    # Run FFmpeg
    frame_path_list = run_ffmpeg(video_path, extract_fps, frame_dir)

    # Run detection
    event_results = run_detection(od_model, event_detectors, frame_path_list, fram_bbox_dir)

    # Extract event result as csv
    extract_event_results(event_dir, video_name, event_detectors, event_results)
