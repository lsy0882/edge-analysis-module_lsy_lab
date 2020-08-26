import json
import os
import cv2

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Please check that you enter parameters and server is turned on")
    parser.add_argument("--video_name", type=str, default="1_360p", help="video name")

    opt = parser.parse_known_args()[0]

    video_name = opt.video_name
    print(video_name)

    video_path = os.path.join(os.getcwd(), "data", "videos", "videos", video_name + ".mp4")
    json_path = os.path.join(os.getcwd(), "data", "videos", "videos", video_name + ".json")
    frame_json_dir = os.path.join(os.getcwd(), "data", "event", video_name)
    frame_json_list = sorted(os.listdir(frame_json_dir))
    fps = 30

    video_frame_count = int(cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = video_frame_count/fps
    video_hour = int(video_duration / 3600)
    video_minute = int(video_duration / 60) - video_hour
    video_second = video_duration - video_minute * 60 - video_hour * 3600
    video_length = "%02d:%02d:%02d" % (video_hour, video_minute, video_second)

    results = {
        "video_name": video_name,
        "length": video_length,
        "frame_num": video_frame_count,
        "event": []
    }

    event_name_list = ["assault", "risk_factors", "pedestrian_abnormal_behavior_fall", "wanderer"]

    frame_events = {}
    for event_name in event_name_list:
        frame_events[event_name] = []

    for i, frame_json_file in enumerate(frame_json_list) :
        frame_json_path = os.path.join(frame_json_dir, frame_json_file)
        json_file = open(frame_json_path, "r")
        frame_json = json.load(json_file)
        json_file.close()

        event_list = frame_json["results"]

        for event in event_list:
            if event["name"] == event_name_list[0]:
                if event["result"] == "warning" :
                    frame_events[event["name"]].append([frame_json["frame_num"], True])
                elif event["result"] == "safe" :
                    frame_events[event["name"]].append([frame_json["frame_num"], False])
            elif event["name"] == event_name_list[1]:
                if len(event["result"]) > 0 :
                    frame_events[event["name"]].append([frame_json["frame_num"], True])
                else :
                    frame_events[event["name"]].append([frame_json["frame_num"], False])
            elif event["name"] == event_name_list[2]:
                if event["result"] == "warning":
                    frame_events[event["name"]].append([frame_json["frame_num"], True])
                elif event["result"] == "safe":
                    frame_events[event["name"]].append([frame_json["frame_num"], False])
            elif event["name"] == event_name_list[3]:
                if len(event["result"]) > 0:
                    frame_events[event["name"]].append([frame_json["frame_num"], True])
                else:
                    frame_events[event["name"]].append([frame_json["frame_num"], False])

    for event_name in event_name_list :
        prev_event = None
        start_frame = 0
        end_frame = None
        for i, event in enumerate(frame_events[event_name]) :
            if i == 0:
                prev_event = event
            elif i == len(frame_events[event_name])-1:
                end_frame = event[0]
                result = {
                    "event": event_name,
                    "start_frame": start_frame,
                    "end_frame": end_frame
                }
                results["event"].append(result)
                print("fin", event[0], event[1])
            else :
                if prev_event[1] == False and event[1] == True:
                    print("new", event[0], event[1])
                    start_frame = event[0]

                elif prev_event[1] == True and event[1] == True :
                    pass
                    print("cont.", event[0], event[1])
                elif prev_event[1] == True and event[1] == False :
                    end_frame = event[0]
                    result = {
                        "event": event_name,
                        "start_frame": start_frame,
                        "end_frame": end_frame
                    }
                    results["event"].append(result)
                    print("fin", event[0], event[1])

                else :
                    print("pass", event[0], event[1])
                prev_event = event

    print("json_path:", json_path)
    with open(json_path, "w") as json_file:
        json.dump(results, json_file, indent="\t")
