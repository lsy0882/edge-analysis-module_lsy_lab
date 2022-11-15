import os
import cv2
import sys
import time
import argparse
import datetime
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from config import config
from utils.test_util import make_result_dir, generate_filter_numbers, load_label, define_object_result, \
    define_event_result, extract_event_results, extract_sequence_results, draw_event
from decoder.CvDecoder import CvDecoder
from utils import Logging
from utils.params_util import *
from utils.time_util import convert_framenumber2timestamp
from utils.visualize import Visualization

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--video_path", type=str, default="media/aihub_01_360p.mp4", help="Video path")
    parser.add_argument("--params_path", type=str, default="config/test_params.yml", help="Model parameter setting path")
    parser.add_argument("--process_time", action='store_true', help="print processing time event models")

    option = parser.parse_known_args()[0]

    video_path = option.video_path
    video_name = video_path.split("/")[-1]
    params_path = option.params_path
    params = load_params(params_path)["settings"]
    model_params = params["model"]
    if ".mp4" in video_path and os.path.exists(str(video_path).replace("_360p", "").replace(".mp4", ".json")):
        video_label_path = str(video_path).replace("_360p", "").replace(".mp4", ".json")
    else :
        video_label_path = None
    video_name = video_path.split("/")[-1]
    process_time = option.process_time
    date = datetime.datetime.now().strftime("%Y%m%d")[2:]

    # parse parameters
    decode_params    = params["decode"]
    extract_fps      = decode_params["extract_fps"]
    result_params    = params["result"]
    result_frame_dir = os.path.join(result_params["video_dir"], str(video_path).replace("_360p", f"_{date}").replace(".mp4", ""))
    origin_frame_dir = os.path.join(result_frame_dir, "frame")
    frame_result_dir = os.path.join(result_frame_dir, "frame_result")
    result_object_video_path = os.path.join(result_params["video_dir"], str(video_name).replace(".mp4", f"_edge_{extract_fps}fps_object.avi"))
    result_event_video_path = os.path.join(result_params["video_dir"], str(video_name).replace(".mp4", f"_edge_{extract_fps}fps_{date}.avi"))
    result_event_csv_path = os.path.join(result_params["video_dir"], str(video_name).replace(".mp4", f"_edge_{extract_fps}fps_{date}.csv"))
    result_sequnece_json_path = os.path.join(result_params["video_dir"], str(video_name).replace(".mp4", f"_edge_{extract_fps}fps_{date}.json"))
    batch_size = model_params['running_model']['batch_size']
    vis = Visualization(params)

    visual_params = params["visualization"]
    model_names = model_params["running_model"]
    object_params = model_params["object_detection"]
    tracker_params = model_params["tracker"]
    event_params = model_params["event"]

    # Logging info
    print(Logging.i("parameter Info:"))
    print(Logging.s("input video path: {}".format(video_path)))
    print(Logging.s("input json path: {}".format(video_label_path)))
    print(Logging.s("decoding parameters"))
    print(Logging.s(f"- mode: {decode_params['decode_mode']}"))
    print(Logging.s(f"- fps: {decode_params['extract_fps']}"))
    print(Logging.s("running model"))
    print(Logging.s(f"- batch size: {batch_size}"))
    print(Logging.s(f"- object detection: {model_params['running_model']['object_detection']}"))
    print(Logging.s(f"- tracker: {model_params['running_model']['tracker']}"))
    print(Logging.s(f"- event: {model_params['running_model']['event']}"))
    print(Logging.s("result parameters"))
    if result_params["save_frame"]:
        print(Logging.s(f"- result frame directory: {result_frame_dir}"))
        make_result_dir(origin_frame_dir)
        make_result_dir(frame_result_dir)
    if result_params["save_video"]:
        make_result_dir(result_params["video_dir"])
        print(Logging.s(f"- final result video path: {result_event_video_path}"))
    if result_params["save_frame"] or result_params["save_video"]:
        print(Logging.s("visual parameters:"))
        print(Logging.s("\tobject:"))
        print(Logging.s(f"\t- result visualize: {visual_params['object']['visual']}"))
        print(Logging.s(f"\t- visualize score threshold: {visual_params['object']['conf_thresh']}"))
        print(Logging.s("\tevent:"))
        print(Logging.s(f"\t- result visualize: {visual_params['event']['visual']}"))

    # load video
    origin_video = CvDecoder(video_path)
    origin_video.load()
    frame_count = int(origin_video.capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(round(origin_video.fps))

    # set object video
    if result_params["save_video"]:
        object_video = cv2.VideoWriter(result_object_video_path, cv2.VideoWriter_fourcc(*'XVID'), extract_fps, (origin_video.width, origin_video.height))

    # load models
    start_time = time.time()
    object_model = config.OBJECT_MODEL[model_names["object_detection"]](object_params)
    end_time = time.time()
    print(Logging.i(f"object detection model({model_names['object_detection']}) model is loaded - {end_time - start_time:.3f} sec"))
    start_time = time.time()
    trackers = []
    event_models = []
    print(Logging.i("loading trackers"))
    for tracker_name in sorted(model_names["tracker"]):
        start_time = time.time()
        tracker = config.TRACKER[tracker_name](tracker_params[tracker_name])
        end_time = time.time()
        trackers.append(tracker)
        print(Logging.s(f"\t{tracker_name} is loaded - {end_time - start_time:.3f} sec"))

    print(Logging.i("loading event models"))
    for event_name in sorted(model_names["event"]):
        start_time = time.time()
        event_model = config.EVENT_MODEL[event_name](event_params[event_name])
        end_time = time.time()
        event_models.append((event_model))
        print(Logging.s(f"\t{event_name} is loaded - {end_time - start_time:.3f} sec"))

    # processing
    filter_frame_numbers = generate_filter_numbers(extract_fps, fps)
    cam_ids = load_label(video_label_path, frame_count)
    event_results = []
    frame_number = 0
    filter_frame_number = 0
    sequence_result = dict()
    end_flag = 0
    process_times = {"total": {
            "object_detection": .0,
            "tracker": [float(0) for tracker in trackers if tracker is not None],
            "event_model": [float(0) for event_model in event_models if event_model is not None]
        },
        "max": {
            "object_detection": .0,
            "tracker": [float(0) for tracker in trackers if tracker is not None],
            "event_model": [float(0) for event_model in event_models if event_model is not None]
        },
        "min": {
            "object_detection": float(10),
            "tracker": [float(10) for tracker in trackers if tracker is not None],
            "event_model": [float(10) for event_model in event_models if event_model is not None]
        }
    }

    total_process_start_time = time.time()
    frame_names = []
    frame_numbers = []
    frames = []
    frame_infos = []
    frame_objectes = []
    while True:
        ret, frame = origin_video.read()
        if not ret:
            end_flag = 1
            for event_detector in event_models:
                sequence_result[event_detector.model_name] = event_detector.merge_sequence(frame_info, end_flag)
            break
        frame_number += 1
        filter_frame_number += 1

        if filter_frame_number in filter_frame_numbers and frame is not None:
            frame_name = "{0:06d}.jpg".format(frame_number)
            if filter_frame_number == 30: filter_frame_number = 0
            if len(cam_ids) == 0: cam_id = "none"
            else: cam_id = cam_ids[frame_number - 1]
            if result_params["save_frame"]: cv2.imwrite(os.path.join(result_frame_dir, frame_name), frame)
            frame_info = {"frame": frame.copy(), "frame_number": frame_number, "cam_id": cam_id, "timestamp": "", "extract_fps": extract_fps}

            frames.append(frame)
            frame_names.append(frame_name)
            frame_numbers.append(frame_number)
            frame_infos.append(frame_info.copy())
            if len(frames) == batch_size or frame_count == frame_number:
                object_start_time = time.time()
                object_results = []
                for frame in frames:
                    object_results.append(object_model.inference_image(frame))
                object_end_time = time.time()

                # Draw object detection results
                for i, (frame, object_result) in enumerate(zip(frames, object_results)):
                    if visual_params["object"]["visual"]:
                        frame_object = vis.draw_bboxes(frame, object_result, visual_params["object"]["conf_thresh"])
                    else:
                        frame_object = frame.copy()
                    if result_params["save_video"]:
                        object_video.write(frame_object)

                process_times["total"]["object_detection"]  += (object_end_time - object_start_time)
                if process_times["max"]["object_detection"] < (object_end_time - object_start_time)/batch_size:
                    process_times["max"]["object_detection"] = (object_end_time - object_start_time)/batch_size
                if process_times["min"]["object_detection"] > (object_end_time - object_start_time)/batch_size:
                    process_times["min"]["object_detection"] = (object_end_time - object_start_time)/batch_size

                frame_length = len(object_results)
                for i in range(frame_length):
                    object_result = object_results.pop(0)
                    frame_number = frame_numbers.pop(0)
                    frame = frames.pop(0)
                    frame_name = frame_names.pop(0)
                    frame_info = frame_infos.pop(0)

                    frame_results = define_object_result(origin_frame_dir, frame_name, video_path, frame_number, extract_fps, fps, object_params["model_name"])
                    frame_results["results"].append({"detection_result": object_result})
                    tracking_results = dict()

                    for i, tracker in enumerate(trackers):
                        start_time = time.time()
                        tracking_result = tracker.update(frame_results.copy())
                        tracking_results[tracker.tracker_name] = tracking_result
                        end_time = time.time()
                        process_times["total"]["tracker"][i] += (end_time - start_time)
                        if process_times["max"]["tracker"][i] < (end_time - start_time):
                            process_times["max"]["tracker"][i] = (end_time - start_time)
                        if process_times["min"]["tracker"][i] > (end_time - start_time):
                            process_times["min"]["tracker"][i] = (end_time - start_time)

                    # Event Detection
                    event_process_times = []
                    event_result = define_event_result(video_path, frame_number, extract_fps, fps)
                    for i, event_model in enumerate(event_models):
                        if event_model.tracker_name == "byte_tracker":
                            tracking_result = tracking_results["byte_tracker"]
                        elif event_model.tracker_name == "sort_tracker":
                            tracking_result = tracking_results["sort_tracker"]
                        else:
                            tracking_result = None

                        start_time = time.time()
                        event_result["event_result"][event_model.model_name] = event_model.inference(frame_info, frame_results, tracking_result)
                        sequence_result[event_model.model_name] = event_model.merge_sequence(frame_info, end_flag)
                        end_time = time.time()

                        event_process_times.append(end_time - start_time)
                        process_times["total"]["event_model"][i] += (end_time - start_time)
                        if process_times["max"]["event_model"][i] < (end_time - start_time):
                            process_times["max"]["event_model"][i] = (end_time - start_time)
                        if process_times["min"]["event_model"][i] > (end_time - start_time):
                            process_times["min"]["event_model"][i] = (end_time - start_time)
                    event_results.append(event_result)

                    # Print log
                    print(Logging.ir("frame number: {:>6}/{}\t/ timestamp: {:>6}"
                        .format(
                            frame_number,
                            frame_count,
                            str(convert_framenumber2timestamp(frame_number, fps)))
                        ), end='')
                    if process_time:
                        print("\t/ process time: ", end="")
                        for i, event_model in enumerate(event_models):
                            print(" {0}: {1:03f}\t/".format(event_model.model_name, event_process_times[i]), end="")
                        print()

    total_process_end_time = time.time()
    origin_video.release()
    if result_params["save_video"]:
        object_video.release()

    print(Logging.i("processing time:"))
    print(Logging.s("\tobject detection({0}) - total: {1:03f}\t/ average: {2:03f}\t/ max: {3:03f}\t / min: {4:03f}".format(
        object_params["model_name"],
        process_times["total"]["object_detection"],
        process_times["total"]["object_detection"]/frame_count,
        process_times["max"]["object_detection"],
        process_times["min"]["object_detection"]
    )))
    print(Logging.s("\ttracker"))
    for i, tracker in enumerate(trackers):
        print(Logging.s("\t\t{0} - total: {1:03f}\t/ average: {2:03f}\t/ max: {3:03f}\t / min: {4:03f}".format(
            tracker.tracker_name,
            process_times["total"]["tracker"][i],
            process_times["total"]["tracker"][i] / frame_count,
            process_times["max"]["tracker"][i],
            process_times["min"]["tracker"][i]
        )))
    print(Logging.s("\tevent detection"))
    for i, event_model in enumerate(event_models):
        print(Logging.s("\t\t{0} - total: {1:03f}\t/ average: {2:03f}\t/ max: {3:03f}\t / min: {4:03f}".format(
            event_model.model_name,
            process_times["total"]["event_model"][i],
            process_times["total"]["event_model"][i] / frame_count,
            process_times["max"]["event_model"][i],
            process_times["min"]["event_model"][i]
        )))
    print(Logging.s("\ttotal process time: {0:03f}".format(total_process_end_time - total_process_start_time)))
    extract_event_results(params, result_event_csv_path, event_results)
    print(Logging.i("event result file is successfully extracted.(path: {})".format(result_event_csv_path)))
    extract_sequence_results(result_sequnece_json_path, sequence_result)
    print(Logging.i("sequence result file is successfully extracted.(path: {})".format(result_sequnece_json_path)))
    if result_params["save_video"]:
        draw_event(vis, result_object_video_path, result_event_video_path, result_sequnece_json_path, extract_fps, params)
        print(Logging.i("sequence result video is successfully generated(path: {})".format(result_event_video_path)))
