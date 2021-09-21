import datetime
import json
import os
import time

from decoder.FFmpegDecoder import FFmpegDecoder
from detector.event.assault.main import AssaultEvent
from detector.event.falldown.main import FalldownEvent
from detector.event.kidnapping.main import KidnappingEvent
from detector.event.obstacle.main import ObstacleEvent
from detector.event.tailing.main import TailingEvent
from detector.event.wanderer.main import WandererEvent
from detector.object_detection.yolov4 import YOLOv4

from utils import PrintLog, Logging
import pycuda.autoinit

path = os.path.dirname(os.path.abspath(__file__))


def load_settings():
    setting_path = os.path.join(path, "settings.json")
    with open(setting_path, 'r') as setting_file:
        dict_settings = json.load(setting_file)
        setting_file.close()
    return parse_settings(dict_settings)


def parse_settings(dict_settings):
    streaming_url = dict_settings['streaming_url']
    fps = dict_settings['fps']
    server_url = dict_settings['server_url']
    od_option = dict_settings['model']['object_detection']
    event_option = dict_settings['model']['event']
    reset_duration = dict_settings['reset_duration']

    print(Logging.i("Settings INFO"))
    print(Logging.s("Streaming URL\t\t\t: {}".format(streaming_url)))
    print(Logging.s("Extract FPS\t\t\t: {}".format(fps)))
    print(Logging.s("Server URL\t\t\t: {}:{}".format(server_url['ip'], server_url['port'])))
    print(Logging.s("Reset duration\t\t\t: {} days").format(reset_duration))
    print(Logging.s("Object detection model INFO: "))
    print(Logging.s("\tModel name\t\t: {}".format(od_option['model_name'])))
    print(Logging.s("\tScore Threshold\t\t: {}".format(od_option['score_thresh'])))
    print(Logging.s("\tNMS Threshold\t\t: {}".format(od_option['nms_thresh'])))
    print(Logging.s("Event model INFO: "))
    print(Logging.s("\tModels\t\t\t: {}".format(event_option)))

    return streaming_url, fps, server_url, od_option, event_option, reset_duration


def load_models(od_option, event_model_names):
    od_model_name = od_option["model_name"]
    score_thresh = od_option["score_thresh"]
    nms_thresh = od_option["nms_thresh"]

    if od_model_name == "yolov4-416":
        od_model = YOLOv4(model=od_model_name, score_threshold=score_thresh, nms_threshold=nms_thresh)
    else:
        od_model = YOLOv4(model=od_model_name, score_threshold=score_thresh, nms_threshold=nms_thresh)

    event_models = []
    PrintLog.i("{} model is loaded".format("Object detection(yolov4)"))

    if event_model_names == "all" or "assault" in event_model_names:
        assault_detection_model = AssaultEvent(debug=True)
        event_models.append(assault_detection_model)
        PrintLog.i("{} model is loaded".format(assault_detection_model.model_name))

    if event_model_names == "all" or "falldown" in event_model_names:
        falldown_detection_model = FalldownEvent(debug=True)
        event_models.append(falldown_detection_model)
        PrintLog.i("{} model is loaded".format(falldown_detection_model.model_name))

    if event_model_names == "all" or "obstacle" in event_model_names:
        obstacle_detection_model = ObstacleEvent(debug=True)
        event_models.append(obstacle_detection_model)
        PrintLog.i("{} model is loaded".format(obstacle_detection_model.model_name))

    if event_model_names == "all" or "kidnapping" in event_model_names:
        kidnapping_detection_model = KidnappingEvent(debug=True)
        event_models.append(kidnapping_detection_model)
        PrintLog.i("{} model is loaded".format(kidnapping_detection_model.model_name))

    if event_model_names == "all" or "tailing" in event_model_names:
        tailing_detection_model = TailingEvent(debug=True)
        event_models.append(tailing_detection_model)
        PrintLog.i("{} model is loaded".format(tailing_detection_model.model_name))

    if event_model_names == "all" or "wanderer" in event_model_names:
        wanderer_detection_model = WandererEvent(debug=True)
        event_models.append(wanderer_detection_model)
        PrintLog.i("{} model is loaded".format(wanderer_detection_model.model_name))

    return od_model, event_models


def set_frame_number(reference_date, frame_number_flag, frame_number, flag_reset_date):
    now = datetime.datetime.now()

    if now == reference_date and frame_number_flag == False:
        frame_number = 0
        frame_number_flag = True
        print(Logging.i("Reset - {}".format(now)))
    elif flag_reset_date == "01:32:00":
        frame_number_flag = False
    else:
        frame_number += 1
    return frame_number_flag, frame_number


def run_detection(video_info, od_model, event_models, reset_duration):
    video_url = video_info["video_path"]
    fps = video_info["fps"]

    now = datetime.datetime.now()
    reference_date = "{}-{}-{} 00:00:00".format(now.year, now.month, now.day + 1)
    flag_reset_date = "{}-{}-{} 23:50:00".format(now.year, now.month, now.day)
    frame_number = 1
    frame_number_flag = False
    end_flag = 0
    process_framecount = 0
    process_time = 0

    decoder = FFmpegDecoder(video_url, fps=fps)
    decoder.load()

    while True:
        start_time = time.time()
        ret, frame = decoder.read()
        if ret == False:
            break

        frame_name = "{0:06d}.jpg".format(frame_number)
        frame_info = {"frame": frame, "frame_number": frame_number}
        results = od_model.inference_by_image(frame)

        dict_result = dict()
        dict_result["image_path"] = frame_name
        dict_result["frame_number"] = frame_number
        dict_result["results"] = []
        dict_result["results"].append({"detection_result": results})

        for event_model in event_models:
            event_model.inference(frame_info, dict_result)
            event_model.merge_sequence(frame_info, end_flag)

        for event_model in event_models:
            if event_model.new_seq_flag == True:
                # print("{}: start sequence".format(event_model.model_name), end='')
                event_model.new_seq_flag = False
                print(Logging.d("Send start time of {} event sequence({})".format(event_model.model_name, datetime.datetime.now())))
                # Send start time of sequence
            if len(event_model.frameseq) > 0:
                sequence = event_model.frameseq.pop()
                # print(" / {}: {}".format(event_model.model_name, sequence), end='')
                print(Logging.d("Send end time of {} event sequence({})".format(event_model.model_name, datetime.datetime.now())))
                # Send end time of sequence
        frame_number += 1

        end_time = time.time()
        process_time += (end_time - start_time)
        process_framecount += 1

        print("\rframe number: {:>6}\t|\tprocess fps: {:>5}\t"
              .format(frame_number,
                      round(process_framecount / process_time), 3), end='')
        print("({:>10}: {:>5} / {:>10}: {:>5} / {:>10}: {:>5} / {:>10}: {:>5} / {:>10}: {:>5})"
            .format(
            event_models[0].model_name, round(event_models[0].analysis_time, 3),
            event_models[1].model_name, round(event_models[1].analysis_time, 3),
            event_models[2].model_name, round(event_models[2].analysis_time, 3),
            event_models[3].model_name, round(event_models[3].analysis_time, 3),
            event_models[4].model_name, round(event_models[4].analysis_time, 3),
        ))


if __name__ == '__main__':
    cctv_url, fps, server_url, od_option, event_option, reset_duration = load_settings()

    video_info = {"video_path": cctv_url, "fps": fps}

    od_model, event_models = load_models(od_option, event_option)
    run_detection(video_info, od_model, event_models, reset_duration)
