import os
import cv2
import argparse

from utils.Visualize import BBoxVisualization
from utils.yolo_classes import get_cls_dict
import json

def draw_event(frame):
    event_frame = frame
    return event_frame

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Please check that you enter parameters and server is turned on.")
    parser.add_argument("--result_path", type=str, default="./result", help="Result directory path")
    parser.add_argument("--result_date", type=str, default="220101", help="Result directory path")

    option = parser.parse_known_args()[0]

    base_dir = option.result_path
    fps = "20"
    date = option.result_date

    video_names = []
    file_list = sorted(os.listdir(base_dir))
    for video_name in file_list:
        if ".avi" in video_name:
            video_names.append(video_name.replace("_bbox.avi", ""))

    for video_name in video_names:

        origin_video_name = video_name + "_bbox.avi"
        event_video_name = video_name + "_edge_" + fps + "fps_" + date + ".mp4"
        json_file_name = video_name + ".json"
        resolution = (640, 360)

        cls_dict = get_cls_dict(15)
        bbox_visualization = BBoxVisualization(cls_dict)

        origin_video_path = os.path.join(base_dir, origin_video_name)
        event_video_path = os.path.join(base_dir, event_video_name)
        json_file_path = os.path.join(base_dir, json_file_name)

        with open(json_file_path, 'r') as json_file:
            result = json.load(json_file)

        results = []
        events = ["assault", "falldown", "kidnapping", "tailing", "wanderer"]

        video_capture = cv2.VideoCapture(origin_video_path)
        frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        video_writer = cv2.VideoWriter(event_video_path, fourcc, 20, resolution)

        for i in range(frame_count+1):
            results.append({'assault': False, 'falldown': False, 'kidnapping': False, 'tailing': False, 'wanderer': False})

        for event in events:
            sequences = result[event]
            for sequence in sequences:
                start_frame = int(sequence['start_frame']/30*20)
                end_frame = int(sequence['end_frame']/30*20)
                for i in range(start_frame, end_frame + 1):
                    results[i][event] = True

        frame_number = 0

        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
            else:
                frame_event = bbox_visualization.put_text(frame, results[frame_number])
                video_writer.write(frame_event)
                print("\rframe number: {}/{} - {}".format(frame_number, frame_count, results[frame_number]), end="")
                frame_number += 1
        print()

        video_capture.release()
        video_writer.release()
        os.rename(json_file_path, json_file_path.replace(".json", "_edge_" + fps  + "fps_" + date +".json"))

