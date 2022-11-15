import os
import json
import cv2
import csv
from utils import Logging
from utils.time_util import convert_framenumber2timestamp

def define_object_result(frame_dir, frame_name, video_path, frame_number, extract_fps, fps, od_model_name):
    dict_result = dict()
    dict_result["image_path"] = os.path.join(frame_dir, frame_name)
    dict_result["cam_address"] = video_path
    dict_result["module"] = od_model_name
    dict_result["frame_number"] = int(frame_number / extract_fps * fps)
    dict_result["timestamp"] = str(convert_framenumber2timestamp(frame_number / extract_fps * fps, fps))
    dict_result["results"] = []
    return dict_result

def define_event_result(video_path, frame_number, extract_fps, fps):
    event_result = dict()
    event_result["cam_address"] = video_path
    event_result["frame_number"] = int(frame_number / extract_fps * fps)
    event_result["timestamp"] = str(convert_framenumber2timestamp(frame_number / extract_fps * fps, fps))
    event_result["event_result"] = dict()
    return event_result

def load_label(json_path, frame_count):
    cam_id_list = []
    if json_path == None or not os.path.exists(json_path):
        return None
    else:
        with open(json_path) as json_file:
            metadata = json.load(json_file)
            events = metadata["event"]
            cam_id_list = ["none" for i in range(frame_count)]

            for i, event in enumerate(events):
                start_frame = int(event["start_frame"])
                end_frame = int(event["end_frame"])
                cam_id = event["cam_id"]
                for e in range(start_frame - 1, end_frame):
                    cam_id_list[e] = cam_id
            json_file.close()
        return cam_id_list

def load_label_json(json_label, frame_count):
    try:
        metadata = json.load(json_label)
        events = metadata["event"]
        cam_id_list = ["none" for i in range(frame_count)]
        for i, event in enumerate(events):
            start_frame = int(event["start_frame"])
            end_frame = int(event["end_frame"])
            cam_id = event["cam_id"]
            for e in range(start_frame - 1, end_frame):
                cam_id_list[e] = cam_id
    except:
        cam_id_list = []
    return cam_id_list

def generate_filter_numbers(extract_fps, fps):
    filter_frame_numbers = []
    if extract_fps != 0 and fps != 0:
        tmp_nums = []
        for i in range(1, fps + 1):
            filter_num = int(i * (extract_fps / fps))
            if filter_num != 0 and filter_num not in tmp_nums:
                tmp_nums.append(filter_num)
                filter_frame_numbers.append(i)
        return filter_frame_numbers
    else:
        return filter_frame_numbers

def make_result_dir(result_dir):
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

def extract_event_results(parmas, result_event_csv_path, event_results):
    try:
        event_model_names = parmas["model"]["running_model"]["event"]
        with open(result_event_csv_path, "w") as event_file:
            csv_writer = csv.writer(event_file)
            if type(event_model_names) == list:
                event_names = event_model_names
            elif event_model_names == "all":
                event_names = ["assault", "falldown", "obstacle", "kidnapping", "tailing", "wanderer"]
            else :
                event_names = [event_model_names]
            name = ["", ""]
            for i, event_model_name in enumerate(event_model_names):
                name.append(event_model_name)

            csv_writer.writerow(name)

            for event_result in event_results:
                row = ["{:>10}".format(event_result["frame_number"]), str(convert_framenumber2timestamp(event_result["frame_number"], 30))]
                for i, event_name in enumerate(event_names):
                    if event_result["event_result"][event_name]:
                        row.append(i+1)
                    else:
                        row.append("")
                csv_writer.writerow(row)
        return True
    except:
        return False

def extract_sequence_results(result_sequnece_json_path, sequence_results):
    try:
        with open(result_sequnece_json_path, "w") as sequence_file:
            json.dump(sequence_results, sequence_file, indent='\t')
        return True
    except:
        return False

def draw_event(vis, pose_video_path, final_result_video_path, json_path, extract_fps, params, events=None):
    if events == None:
        events = params['model']['running_model']['event']
    with open(json_path, 'r') as json_file:
        result = json.load(json_file)
    results = []

    video_capture = cv2.VideoCapture(pose_video_path)
    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    width = int(round(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
    height = int(round(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    video_writer = cv2.VideoWriter(final_result_video_path, fourcc, int(extract_fps), (width, height))
    for i in range(frame_count + 1):
        results.append({'assault': False, 'falldown': False, 'kidnapping': False, 'tailing': False, 'wanderer': False})
    for event in events:
        sequences = result[event]
        for sequence in sequences:
            start_frame = int(sequence['start_frame'] / 30 * int(extract_fps))
            end_frame = int(sequence['end_frame'] / 30 * int(extract_fps))
            for i in range(start_frame, end_frame + 1):
                try:
                    results[i][event] = True
                except:
                    pass
    frame_number = 0
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        else:
            frame_event = vis.put_text(frame, results[frame_number], events)
            video_writer.write(frame_event)
            print(Logging.ir("frame number: {:>6}/{} - {}".format(frame_number, frame_count, results[frame_number])), end="")
            frame_number += 1
    print()

    video_capture.release()
    video_writer.release()
