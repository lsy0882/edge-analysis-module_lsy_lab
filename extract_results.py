import datetime

import pycuda.autoinit
import argparse
import json
import os
import cv2
import csv

from decoder.FFmpegDecoder import FFmpegDecoder
from detector.event.assault.main import AssaultEvent
from detector.event.falldown.main import FalldownEvent
from detector.event.kidnapping.main import KidnappingEvent
from detector.event.obstacle.main import ObstacleEvent
from detector.event.tailing.main import TailingEvent
from detector.event.wanderer.main import WandererEvent
from detector.object_detection.yolov4.yolov4 import YOLOv4

from utils.time_util import convert_framenumber2timestamp
from utils import Logging
from utils.yolo_classes import get_cls_dict
from utils.Visualize import BBoxVisualization

def split_model_names(model_names):
    return model_names.split(",")

def load_video(video_path, extract_fps):
    capture = cv2.VideoCapture(video_path)
    framecount = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(round(capture.get(cv2.CAP_PROP_FPS)))

    print(Logging.i("Extract information"))
    print(Logging.s("video path: {}".format(video_path)))
    print(Logging.s("video fps: {}".format(fps)))
    print(Logging.s("video framecount: {}".format(framecount)))
    print(Logging.s("extract fps: {}".format(extract_fps)))
    print(Logging.s("extract frame number: {}".format(int(framecount/(fps/extract_fps)))))

    return capture, framecount, fps


def load_models(od_model_name="yolov4-416", score_threshold=0.5, nms_threshold=0.3, event_model_names="all"):
    if od_model_name == "yolov4-416":
        od_model = YOLOv4(model=od_model_name, score_threshold=score_threshold, nms_threshold=nms_threshold)
    else :
        od_model = YOLOv4(model=od_model_name, score_threshold=score_threshold, nms_threshold=nms_threshold)

    print(Logging.i("YOLO detector information"))
    print(Logging.s("model name: {}".format(od_model_name)))
    print(Logging.s("score threshold: {}".format(score_threshold)))
    print(Logging.s("nms threshold: {}".format(nms_threshold)))

    event_detectors = []
    print(Logging.i("{} model is loaded".format("Object detection(yolov4)")))

    splited_model_names = split_model_names(event_model_names)

    if event_model_names == "all" or "assault" in splited_model_names:
        assault_detection_model = AssaultEvent()
        event_detectors.append(assault_detection_model)
        print(Logging.i("{} model is loaded".format(assault_detection_model.model_name)))

    if event_model_names == "all" or "falldown" in splited_model_names:
        falldown_detection_model = FalldownEvent()
        event_detectors.append(falldown_detection_model)
        print(Logging.i("{} model is loaded".format(falldown_detection_model.model_name)))

    if event_model_names == "all" or "obstacle" in splited_model_names:
        obstacle_detection_model = ObstacleEvent()
        event_detectors.append(obstacle_detection_model)
        print(Logging.i("{} model is loaded".format(obstacle_detection_model.model_name)))

    if event_model_names == "all" or "kidnapping" in splited_model_names:
        kidnapping_detection_model = KidnappingEvent()
        event_detectors.append(kidnapping_detection_model)
        print(Logging.i("{} model is loaded".format(kidnapping_detection_model.model_name)))

    if event_model_names == "all" or "tailing" in splited_model_names:
        tailing_detection_model = TailingEvent()
        event_detectors.append(tailing_detection_model)
        print(Logging.i("{} model is loaded".format(tailing_detection_model.model_name)))

    if event_model_names == "all" or "wanderer" in splited_model_names:
        wanderer_detection_model = WandererEvent()
        event_detectors.append(wanderer_detection_model)
        print(Logging.i("{} model is loaded".format(wanderer_detection_model.model_name)))

    return od_model, event_detectors


def make_result_dir(result_dir, video_name, save_frame_result):
    frame_dir = os.path.join(result_dir, video_name.split(".mp4")[0], "frame")
    fram_bbox_dir = os.path.join(result_dir, video_name.split(".mp4")[0], "fram_bbox")
    json_dir = os.path.join(result_dir, video_name.split(".mp4")[0], "json")
    event_dir = os.path.join(result_dir)

    if save_frame_result:
        if not os.path.exists(frame_dir):
            os.makedirs(frame_dir)
        if not os.path.exists(fram_bbox_dir):
            os.makedirs(fram_bbox_dir)
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)

    return frame_dir, fram_bbox_dir, json_dir, event_dir


def run_detection(video_info, od_model, score_threshold, event_detectors, frame_dir, json_dir, bbox_video_path, save_frame_result):
    print(Logging.i("Processing..."))
    fps = video_info["fps"]
    framecount = video_info["framecount"]
    extract_fps = video_info["extract_fps"]

    decoder = FFmpegDecoder(video_info["video_path"], fps=extract_fps)
    decoder.load()

    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    video_writer = cv2.VideoWriter(bbox_video_path, fourcc, 20, (640, 360))

    expected_framecount = int(framecount / fps * extract_fps)
    frame_number = 0
    event_results = []
    cls_dict = get_cls_dict(15)
    bbox_visualization = BBoxVisualization(cls_dict)
    sequence_result = dict()
    end_flag =0

    while True:
        ret, frame = decoder.read()
        if ret == False:
            end_flag =1
            for event_detector in event_detectors:
                sequence_result[event_detector.model_name] = event_detector.merge_sequence(None, end_flag)
            break

        frame_number += 1
        frame_name = "{0:06d}.jpg".format(frame_number)
        frame_info = {"frame": frame, "frame_number": int(frame_number / extract_fps * fps)}
        results = od_model.inference_by_image(frame)

        dict_result = dict()
        dict_result["image_path"] = os.path.join(frame_dir, frame_name)
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

        frame_bbox = bbox_visualization.draw_bboxes(frame, results)
        video_writer.write(frame_bbox)

        for event_detector in event_detectors:
            event_result["event_result"][event_detector.model_name] = event_detector.inference(frame_info, dict_result, score_threshold[event_detector.model_name])
            sequence_result[event_detector.model_name] = event_detector.merge_sequence(frame_info, end_flag)
        event_results.append(event_result)

        print(Logging.ir("frame number: {:>6}/{}\t/ extract frame number: {:>6}\t/ timestamp: {:>6}"
            .format(
                frame_number,
                expected_framecount,
                int(frame_number / extract_fps * fps),
                str(convert_framenumber2timestamp(frame_number / extract_fps * fps, fps)))
            ), end='')

        if save_frame_result:
            json_result_file = open(os.path.join(json_dir, frame_name.split(".jpg")[0] + ".json"), "w")
            json.dump(dict_result, json_result_file, indent=4)
            json_result_file.close()
    video_writer.release()
    print(Logging.inl("Extraction is successfully completed(framecount: {})".format(frame_number)))
    if os.path.exists(bbox_video_path) :
        print(Logging.i("BBox video is successfully generated(path: {})".format(bbox_video_path)))
    else :
        print(Logging.i("BBox video is failed to generated."))
    return event_results, sequence_result


def extract_event_results(event_model_names, event_dir, video_name, event_detectors, event_results):
    event_csv_file_path = os.path.join(event_dir, "..", video_name.split(".mp4")[0] + ".csv")
    with open(event_csv_file_path, "w") as event_file:
        csv_writer = csv.writer(event_file)
        if type(event_model_names) == list:
            event_names = event_model_names
        elif event_model_names == "all":
            event_names = ["assault", "falldown", "obstacle", "kidnapping", "tailing", "wanderer"]
        else :
            event_names = [event_model_names]
        name = ["", ""]
        for i, event_detector in enumerate(event_detectors):
            name.append(event_detector.model_name)

        csv_writer.writerow(name)

        for event_result in event_results:
            row = ["{:>10}".format(event_result["frame_number"]), str(convert_framenumber2timestamp(event_result["frame_number"], 30))]
            for i, event_name in enumerate(event_names):
                if event_result["event_result"][event_name]:
                    row.append(i+1)
                else:
                    row.append("")
            csv_writer.writerow(row)
    print(Logging.i("Event result file is successfully extracted.(path: {})".format(event_csv_file_path)))


def extract_sequence_results(event_dir, video_name, sequence_results):
    sequence_json_file_path = os.path.join(event_dir, video_name.replace(".mp4", ".json"))
    with open(sequence_json_file_path, "w") as sequence_file:
        json.dump(sequence_results, sequence_file, indent='\t')

    print(Logging.i("Sequence result file is successfully extracted.(path: {})".format(sequence_json_file_path)))
    return sequence_json_file_path


def draw_event(bbox_video_path, sequence_json_path, extract_fps, events):
    print(Logging.i("Generate result(video and json)"))
    date = datetime.datetime.now().strftime("%Y%m%d")[2:]

    origin_video_path = bbox_video_path
    event_video_path = bbox_video_path.replace("_bbox.avi", "") + "_edge_" + str(extract_fps) + "fps_" + date + ".mp4"
    json_file_path = bbox_video_path.replace("_bbox.avi", "") + "_edge_" + str(extract_fps) + "fps_" + date + ".json"
    resolution = (640, 360)

    cls_dict = get_cls_dict(15)
    bbox_visualization = BBoxVisualization(cls_dict)

    with open(sequence_json_path, 'r') as json_file:
        result = json.load(json_file)

    results = []

    video_capture = cv2.VideoCapture(origin_video_path)
    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video_writer = cv2.VideoWriter(event_video_path, fourcc, 20, resolution)

    for i in range(frame_count + 1):
        results.append({'assault': False, 'falldown': False, 'kidnapping': False, 'tailing': False, 'wanderer': False})

    for event in events:
        sequences = result[event]
        for sequence in sequences:
            start_frame = int(sequence['start_frame'] / 30 * 20)
            end_frame = int(sequence['end_frame'] / 30 * 20)
            for i in range(start_frame, end_frame + 1):
                results[i][event] = True

    frame_number = 0

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        else:
            frame_event = bbox_visualization.put_text(frame, results[frame_number], events)
            video_writer.write(frame_event)
            print(Logging.ir("frame number: {:>6}/{} - {}".format(frame_number, frame_count, results[frame_number])), end="")
            frame_number += 1
    print()

    video_capture.release()
    video_writer.release()
    os.rename(sequence_json_path, json_file_path)
    print(Logging.i("Sequence result video is successfully generated(path: {})".format(event_video_path)))
    print(Logging.i("Sequence json file is successfully generated(path: {})".format(json_file_path)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--video_path", type=str, default="videos/001_360.mp4", help="Video path")
    parser.add_argument("--fps", type=int, default=20, help="FPS of extraction frame ")
    parser.add_argument("--od_model_name", type=str, default="yolov4-416", help="Object detection model name")
    parser.add_argument("--nms_th", type=float, default=0.1, help="Object detection nms threshold")
    parser.add_argument("--assault_score_th", type=float, default=0.1, help="Object score threshold of assault model")
    parser.add_argument("--falldown_score_th", type=float, default=0.5, help="Object score threshold of falldown model")
    parser.add_argument("--kidnapping_score_th", type=float, default=0.5, help="Object score threshold of kidnapping model")
    parser.add_argument("--tailing_score_th", type=float, default=0.5, help="Object score threshold of tailing model")
    parser.add_argument("--wanderer_score_th", type=float, default=0.5, help="Object score threshold of wanderer model")
    parser.add_argument("--event_model", type=str, default="all", help="Event model names")
    parser.add_argument("--result_dir", type=str, default="./result", help="Directory path of results and frame")
    parser.add_argument("--save_frame_result", action='store_true', help="Is save frame result")

    option = parser.parse_known_args()[0]

    video_path = option.video_path
    video_name = video_path.split("/")[-1]
    extract_fps = option.fps
    nms_threshold = option.nms_th
    score_threshold = {
        "assault": option.assault_score_th,
        "falldown": option.falldown_score_th,
        "kidnapping": option.kidnapping_score_th,
        "tailing": option.tailing_score_th,
        "wanderer": option.wanderer_score_th,
    }
    od_model_name = option.od_model_name
    event_model_names = option.event_model
    result_dir = option.result_dir
    save_frame_result = option.save_frame_result

    bbox_video_path = os.path.join(result_dir, video_name.split(".mp4")[0] + "_bbox.avi")
    print(Logging.i("Argument Info:"))
    print(Logging.s("input video path: {}".format(video_path)))
    print(Logging.s("extract fps: {}".format(extract_fps)))
    print(Logging.s("nms threshold: {}".format(nms_threshold)))
    print(Logging.s("object detection model name: {}".format(od_model_name)))
    print(Logging.s("event model names: {}".format(event_model_names)))
    print(Logging.s("result directory path: {}".format(result_dir)))
    print(Logging.s("bbox video path: {}".format(bbox_video_path)))
    print(Logging.s("score threshold:"))
    for event_name in split_model_names(event_model_names):
        print(Logging.s("    {}: {}".format(event_name, score_threshold[event_name])))

    # Load Video
    capture, framecount, fps = load_video(video_path, extract_fps)

    # Load Object Detection & Event Detection models
    od_model, event_detectors = load_models(od_model_name, score_threshold=0.0, nms_threshold=nms_threshold, event_model_names=event_model_names)

    # Result Directory info
    frame_dir, fram_bbox_dir, json_dir, event_dir = make_result_dir(result_dir, video_name, save_frame_result)

    # Run detection
    video_info = {"video_path": video_path, "fps": fps, "framecount": framecount, 'extract_fps': extract_fps}
    event_results, sequence_results = run_detection(video_info, od_model, score_threshold, event_detectors, frame_dir, json_dir, bbox_video_path, save_frame_result)

    # Extract event result as csv
    if save_frame_result:
        extract_event_results(split_model_names(event_model_names), event_dir, video_name, event_detectors, event_results)

    # Extract sequence result as json
    sequence_json_path = extract_sequence_results(event_dir, video_name, sequence_results)

    # Draw event in bbox video
    draw_event(bbox_video_path, sequence_json_path, extract_fps, split_model_names(event_model_names))