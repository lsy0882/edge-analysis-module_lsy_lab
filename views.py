import datetime

from flask import Flask, render_template, send_from_directory, request
from urls import urls
from utils.setting_utils import *
from utils.task_utils import *
from config import config
import os
import json
import shutil
import ast
import subprocess

from tasks import *

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('static/js', path)


@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('static/css', path)


@app.route('/cdn/<path:path>')
def send_cdn(path):
    return send_from_directory('static/cdn', path)


@app.route('/media/<path:path>')
def send_media(path):
    return send_from_directory('static/media', path)


@app.route('/start_thread/')
def start_thread() :

    return


@app.route(urls["ajax_stats"], methods=["GET"])
def ajax_get_stats():
    try:
        popen = subprocess.Popen(["tegrastats"], stdout=subprocess.PIPE, universal_newlines=True)
        output = subprocess.check_output(("head", "-n 1"), stdin=popen.stdout).decode("UTF-8").split(" ")

        # Memory info
        ram = output[1].replace("MB", "").split("/")
        swap = output[5].replace("MB", "").split("/")

        # CPU info
        tmp = output[9].replace("[", "").replace("]", "").split(",")
        cpu = [int(cpu_usage.split("@")[0].replace("%", "")) for cpu_usage in tmp]
        cpu_clock = [int(cpu_usage.split("@")[1]) for cpu_usage in tmp]

        # GPU info
        gpu = output[13].split("@")
        gpu_usage = int(gpu[0].replace("%", ""))
        gpu_clock = int(gpu[1])

        # Temp info
        cpu_temp = float(output[25].replace("CPU@", "").split("C")[0])
        gpu_temp = float(output[22].replace("GPU@", "").split("C")[0])
        device_temp = float(output[26].replace("thermal@", "").split("C")[0])

        # Power info
        total_power = int(output[28].split("/")[0])
        cpu_gpu_cv_power = int(output[30].split("/")[0])
        soc_power = int(output[32].replace("\n", "").split("/")[0])

        result = {
            "ret": True,
            "CPU": {
                "usage": {
                    "value": cpu,
                    "unit": "%"
                },
                "clock": {
                    "value": cpu_clock,
                    "unit": "MHz"
                },
            },
            "MEM": {
                "RAM": {"CUR": ram[0], "MAX": ram[1]},
                "SWAP": {"CUR": swap[0], "MAX": swap[1]},
                "unit": "MB"
            },
            "GPU": {
                "usage": {
                    "value": gpu_usage,
                    "unit": "%"
                },
                "clock": {
                    "value": gpu_clock,
                    "unit": "MHz"
                }
            },
            "DISK": None,
            "TEMP": {
                "CPU": cpu_temp,
                "GPU": gpu_temp,
                "DEVICE": device_temp,
                "unit": "C"
            },
            "POWER": {
                "TOTAL": total_power,
                "CPU GPU CV": cpu_gpu_cv_power,
                "SOC": soc_power,
                "unit": "mW"
            },
            "message": "Device status is successfully parsed."
        }
    except:
        result = {"ret": False, "message": "Cannot parse device status."}

    try:
        main_disk = shutil.disk_usage("/")
        usb_disk = shutil.disk_usage("/media/nvidia/external/")

        result["DISK"]= {
            "main": {
                "total": main_disk.total/(2 ** 30),
                "used": main_disk.used / (2 ** 30),
                "free": main_disk.free / (2 ** 30),
                "unit": "GiB"
            },
            "external": {
                "total": usb_disk.total / (2 ** 30),
                "used": usb_disk.used / (2 ** 30),
                "free": usb_disk.free / (2 ** 30),
                "unit": "GiB"
            }
        }

        result["message"] += " Disk usage is successfully parsed."
    except:
        result["message"] += " Cannot parse disk usage."

    return json.dumps(result)


@app.route(urls["ajax_get_settings"], methods=["GET"])
def ajax_get_settings():
    settings_path = os.path.join(os.getcwd(), "config", "settings.yml")
    settings = load_settings(settings_path)

    return json.dumps(settings)


@app.route(urls["ajax_set_settings"], methods=["POST"])
def ajax_set_settings():
    settings = ast.literal_eval(json.dumps(request.form))
    format_settings = {
        "settings": {
            "cctv_info": {
                "streaming_url": str(settings["streaming_url"]),
                "streaming_type": str(settings["streaming_type"]),
                "cam_id": settings["cam_id"]
            },
            "communication_info": {
                "server_url": {
                    "ip": str(settings["archive_server_ip"]),
                    "port": int(settings["archive_server_port"]),
                }
            },
            "decode_option": {
                "fps": int(settings["decode_fps"])
            },
            "model": {
                "object_detection": {
                    "model_name": str(settings["od_model_name"]),
                    "score_threshold": float(settings["od_score_threshold"]),
                    "nms_threshold": float(settings["od_nms_threshold"]),
                },
                "tracker": {
                    "tracker_names": settings["tracker_names"].split(","),
                    "byte_tracker": {
                        "score_threshold": float(settings["byte_tracker_score_threshold"]),
                        "track_threshold": float(settings["byte_tracker_track_threshold"]),
                        "track_buffer": int(settings["byte_tracker_track_buffer"]),
                        "match_threshold": float(settings["byte_tracker_match_threshold"]),
                        "min_box_area": int(settings["byte_tracker_min_box_area"]),
                        "frame_rate": int(settings["byte_tracker_frame_rate"]),
                    },
                    "sort_tracker": {
                        "score_threshold": float(settings["sort_tracker_score_threshold"]),
                        "max_age": int(settings["sort_tracker_max_age"]),
                        "min_hits": int(settings["sort_tracker_min_hits"])
                    }
                },
                "event": {
                    "event_names": settings["event_names"].split(","),
                    "event_options": {
                        "assault": {
                            "score_threshold": float(settings["assault_score_threshold"]),
                            "tracker": str(settings["assault_tracker"]),
                        },
                        "falldown": {
                            "score_threshold": float(settings["falldown_score_threshold"]),
                            "tracker": str(settings["falldown_tracker"]),
                        },
                        "kidnapping": {
                            "score_threshold": float(settings["kidnapping_score_threshold"]),
                            "tracker": str(settings["kidnapping_tracker"]),
                        },
                        "tailing": {
                            "score_threshold": float(settings["tailing_score_threshold"]),
                            "tracker": str(settings["tailing_tracker"]),
                        },
                        "wanderer": {
                            "score_threshold": float(settings["wanderer_score_threshold"]),
                            "tracker": str(settings["wanderer_tracker"]),
                        }
                    }
                }
            }
        }
    }
    try:
        settings_path = os.path.join(os.getcwd(), "config", "settings.yml")
        save_settings(format_settings, settings_path)
        result = {
            "ret": True
        }
    except:
        result = {
            "ret": False
        }

    return json.dumps(result)


@app.route(urls["ajax_run_task"], methods=["GET"])
def ajax_run_task():
    result = {"ret": False}

    try:
        task = run_module.delay()
        result["ret"] = True
        result["type"] = "celery"
    except:
        task = run_module()
        result["ret"] = True
        result["type"] = "flask"
    current_time = datetime.datetime.now()
    result["id"] = task.id
    result["state"] = "PROGRESS"
    result["start_time"] = str(current_time)
    result["start_time_num"] = float(current_time.timestamp())
    save_task_info(result, config.TASK_INFO_PATH)

    return json.dumps(result)


@app.route(urls["ajax_get_task"], methods=["GET"])
def ajax_get_task():
    task_info = get_task_info(config.TASK_INFO_PATH)["task"]
    ret = get_task_state(task_info["id"], task_info["state"])
    if not ret:
        task_info = {
            "ret": False,
            "id": None,
            "state": None,
            "start_time": None,
            "start_time_num": None
        }
    else:
        task_info["ret"] = True

    return json.dumps(task_info)


@app.route(urls["ajax_delete_task"], methods=["GET"])
def ajax_delete_task():
    task_info = get_task_info(config.TASK_INFO_PATH)["task"]
    ret = del_task(task_info["id"])
    print(ret)
    if ret:
        result = {}
        result["type"] = ''
        result["id"] = ''
        result["state"] = ''
        result["start_time"] = ''
        result["start_time_num"] = 0
        save_task_info(result, config.TASK_INFO_PATH)
    return json.dumps({})
