from Config.config import DEBUG
from Config.config import DISPLAY
from Modules.tailing_kidnapping.main import Tailing_Kidnapping
from Modules.obstacle.main import Obstacle
from Modules.FightDetection.main import FightDetection
from Modules.WanderDetection.main import WanderDetection
from threading import Thread
import socket
from datetime import datetime
import ast
import time
import cv2
import json

class AnalysisServer:
    def __init__(self, host="127.0.0.1", port=10001, debug=False, display=False, show_scale=1):
        self.host = host
        self.port = port
        self.debug = debug
        self.display = display
        self.show_scale = show_scale

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.models = []

        fight_detection_model = FightDetection(self.debug)
        print("INFO: {} - {} model is loaded".format(datetime.now(), fight_detection_model.model_name))

        wander_detection_model = WanderDetection(self.debug)
        print("INFO: {} - {} model is loaded".format(datetime.now(), wander_detection_model.model_name))

        obstacle_model = Obstacle(self.debug)
        print("INFO: {} - {} model is loaded".format(datetime.now(), obstacle_model.model_name))

        tailing_kidnapping_model = Tailing_Kidnapping(self.debug)
        print("INFO: {} - {} model is loaded".format(datetime.now(), tailing_kidnapping_model.model_name))

        self.models.append(fight_detection_model)
        self.models.append(wander_detection_model)
        self.models.append(obstacle_model)
        self.models.append(tailing_kidnapping_model)
        print("INFO: {} - Server is Initialized".format(datetime.now()))


    def run_server(self):
        self.client_socket, self.addr = self.server_socket.accept()
        print("INFO: {} - Connected by {}".format(datetime.now(), self.addr))
        while True:
            data = self.client_socket.recv(10240) # bufSize 1KB->5KB
            if not data:
                break
            json_data = ast.literal_eval(str(data))
            print("INFO: {} - Received from {}\t".format(datetime.now(), self.addr))

            threads = []
            for model in self.models:
                thread = Thread(target=model.analysis_from_json, args=(json_data,))
                threads.append(thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            results = []
            for model in self.models:
                result = {
                    "name": model.model_name,
                    "time" : model.analysis_time,
                    "result": model.result
                }
                results.append(result)

            data = json_data.decode('utf-8').replace("'", '"')  # byte to string
            json_data = json.loads(data)
            print("INFO: {} - {} Results analyzed is \"{}\"".format(datetime.now(), json_data["frame_num"], results))

            if self.debug:
                print("\tAnalysis Time")
                total_time = 0
                total_time += json_data["analysis_time"]
                print("\t\tObject detection time: {}".format(json_data["analysis_time"]))
                for model in self.models:
                    total_time += model.analysis_time
                    print("\t\tname:", model.model_name, "\ttime:",model.analysis_time)
                print("\t\tTotal analysis time: {}".format(total_time))
            if self.display:
                self.show(json_data, self.show_scale)
            self.client_socket.sendall("INFO: {} - Successfully received".format(datetime.now()).encode())

    def show(self, json_data, scale):
        frame = cv2.imread(json_data["image_path"])
        frame = cv2.resize(frame, (frame.shape[1] * scale, frame.shape[0] * scale), interpolation=cv2.INTER_AREA)

        results = json_data["results"][0]["detection_result"]
        for obj in results :
            if obj["label"][0]["description"] == "person" :
                color = (0, 255, 0)
                x = obj["position"]["x"] * scale
                y = obj["position"]["y"] * scale
                w = obj["position"]["w"] * scale
                h = obj["position"]["h"] * scale

                cv2.rectangle(frame, (x,y), (x+w,y+h), color, 2)
                cv2.putText(frame, "{}: {}%".format(obj["label"][0]["description"], int(obj["label"][0]["score"])), (x, y-20), cv2.FONT_HERSHEY_PLAIN, 2, color, 1, cv2.LINE_AA)

        for i, model in enumerate(self.models):
            model_name = model.model_name
            result = model.result
            cv2.putText(frame, "{}: {}".format(model_name, result), (30, 30 + i * 40), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 1, cv2.LINE_AA)
        cv2.imshow("cam_{}".format(json_data["cam_id"]), frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            return

    def shutdown_server(self):
        self.client_socket.close()
        self.server_socket.close()