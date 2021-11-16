import argparse
import json
import os
import time

import cv2
import csv

import pycuda.autoinit

from decoder.FFmpegDecoder import FFmpegDecoder
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


def load_video(video_path, extract_fps):
    capture = cv2.VideoCapture(video_path)
    framecount = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(round(capture.get(cv2.CAP_PROP_FPS)))

    PrintLog.i("Extract information\n"
               "\tvideo path: {}\n"
               "\tvideo fps: {}\n"
               "\tvideo framecount: {}\n"
               "\textract fps: {}\n"
               "\textract frame number: {}"
               .format(video_path, fps, framecount, extract_fps, int(framecount/(fps/extract_fps))))
    return capture, framecount, fps

def load_models(od_model_name="yolov4-416", score_threshold=0.5, nms_threshold=0.3, event_model_names="all"):
    if od_model_name == "yolov4-416":
        od_model = YOLOv4(model=od_model_name, score_threshold=score_threshold, nms_threshold=nms_threshold)
    else :
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
        assault_detection_model = AssaultEvent(debug=True)
        event_detectors.append(assault_detection_model)
        PrintLog.i("{} model is loaded".format(assault_detection_model.model_name))

    if event_model_names == "all" or "falldown" in splited_model_names:
        falldown_detection_model = FalldownEvent(debug=True)
        event_detectors.append(falldown_detection_model)
        PrintLog.i("{} model is loaded".format(falldown_detection_model.model_name))

    if event_model_names == "all" or "obstacle" in splited_model_names:
        obstacle_detection_model = ObstacleEvent(debug=True)
        event_detectors.append(obstacle_detection_model)
        PrintLog.i("{} model is loaded".format(obstacle_detection_model.model_name))

    if event_model_names == "all" or "kidnapping" in splited_model_names:
        kidnapping_detection_model = KidnappingEvent(debug=True)
        event_detectors.append(kidnapping_detection_model)
        PrintLog.i("{} model is loaded".format(kidnapping_detection_model.model_name))

    if event_model_names == "all" or "tailing" in splited_model_names:
        tailing_detection_model = TailingEvent(debug=True)
        event_detectors.append(tailing_detection_model)
        PrintLog.i("{} model is loaded".format(tailing_detection_model.model_name))

    if event_model_names == "all" or "wanderer" in splited_model_names:
        wanderer_detection_model = WandererEvent(debug=True)
        event_detectors.append(wanderer_detection_model)
        PrintLog.i("{} model is loaded".format(wanderer_detection_model.model_name))

    return od_model, event_detectors


def run_detection(video_info, od_model, event_detectors):
    fps = video_info["fps"]
    framecount = video_info["framecount"]
    extract_fps = video_info["extract_fps"]

    decoder = FFmpegDecoder(video_info["video_path"], fps=extract_fps)
    decoder.load()

    expected_framecount = int(framecount / fps * extract_fps)
    frame_number = 0
    event_results = []
    sequence_result = dict()
    end_flag = 0
    process_framecount = 0
    process_time = 0

    while True:
        start_time = time.time()
        ret, frame = decoder.read()
        if ret == False:
            end_flag = 1
            for event_detector in event_detectors:
                sequence_result[event_detector.model_name] = event_detector.merge_sequence(frame_info, end_flag)
            break

        frame_number += 1
        frame_name = "{0:06d}.jpg".format(frame_number)
        frame_info = {"frame": frame, "frame_number": int(frame_number / extract_fps * fps)}
        results = od_model.inference_by_image(frame)

        dict_result = dict()
        dict_result["image_path"] = frame_name
        dict_result["cam_address"] = video_path
        dict_result["module"] = od_model_name
        dict_result["frame_number"] = int(frame_number / extract_fps * fps)
        dict_result["timestamp"] = str(convert_framenumber2timestamp(frame_number / extract_fps * fps, fps))
        dict_result["results"] = []
        dict_result["results"].append({"detection_result": results})

        event_result = dict()
        event_result["cam_address"] = video_path
        event_result["frame_number"] = int(frame_number / extract_fps * fps)
        event_result["timestamp"] = str(convert_framenumber2timestamp(frame_number / extract_fps * fps, fps))
        event_result["event_result"] = dict()

        for event_detector in event_detectors:
            event_result["event_result"][event_detector.model_name] = event_detector.inference(frame_info, dict_result)
            sequence_result[event_detector.model_name] = event_detector.merge_sequence(frame_info, end_flag)
        event_results.append(event_result)
        end_time = time.time()
        process_time += (end_time - start_time)
        process_framecount += 1

        print("\rframe number: {:>6}/{:>4}\t|\tprocess fps: {:>5}\t"
              .format(frame_number,
                      expected_framecount,
                      round(process_framecount/process_time), 3), end='')
        print("({:>10}: {:>5} / {:>10}: {:>5} / {:>10}: {:>5} / {:>10}: {:>5} / {:>10}: {:>5})"
              .format(
                  event_detectors[0].model_name, round(event_detectors[0].analysis_time, 3),
                  event_detectors[1].model_name, round(event_detectors[1].analysis_time, 3),
                  event_detectors[2].model_name, round(event_detectors[2].analysis_time, 3),
                  event_detectors[3].model_name, round(event_detectors[3].analysis_time, 3),
                  event_detectors[4].model_name, round(event_detectors[4].analysis_time, 3),
              ))

    return event_results, sequence_result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--video_path", type=str, default="videos/360p_01.mp4", help="Video path")
    option = parser.parse_known_args()[0]

    video_path = option.video_path
    video_name = video_path.split("/")[-1]
    extract_fps = 20
    score_threshold = 0.5
    nms_threshold = 0.1
    od_model_name = "yolov4-416"
    event_model_names = "assault,falldown,kidnapping,tailing,wanderer"
    PrintLog.i("Argument Info:\n"
               "\tinput video path: {}\n"
               "\textract fps: {}\n"
               "\tscore threshold: {}\n"
               "\tnms threshold: {}\n"
               "\tobject detection model name: {}\n"
               "\tevent model names: {}\n"
               .format(video_path, extract_fps, score_threshold, nms_threshold, od_model_name,
                                              event_model_names))

    # Load Video
    capture, framecount, fps = load_video(video_path, extract_fps)

    # Load Object Detection & Event Detection models
    od_model, event_detectors = load_models(od_model_name, score_threshold=score_threshold, nms_threshold=nms_threshold,
                                            event_model_names=event_model_names)

    # Run detection
    video_info = {"video_path": video_path, "fps": fps, "framecount": framecount, 'extract_fps': extract_fps}
    event_results, sequence_results = run_detection(video_info, od_model, event_detectors)
