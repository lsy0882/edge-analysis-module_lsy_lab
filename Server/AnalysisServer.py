from Modules.tailing_kidnapping.main import Tailing_Kidnapping
from Modules.obstacle.main import Obstacle
from threading import Thread
import socket
from datetime import datetime
import ast

class AnalysisServer:
    def __init__(self, host="127.0.0.1", port=10001):
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.models = []

        dummy_model = Obstacle()
        print("INFO: {} - {} model is loaded".format(datetime.now(), dummy_model.model_name))

        dummy2_model = Tailing_Kidnapping()
        print("INFO: {} - {} model is loaded".format(datetime.now(), dummy2_model.model_name))

        self.models.append(dummy_model)
        self.models.append(dummy2_model)
        print("INFO: {} - Server is Initialized".format(datetime.now()))


    def run_server(self):
        self.client_socket, self.addr = self.server_socket.accept()
        print("INFO: {} - Connected by {}".format(datetime.now(), self.addr))
        while True:
            data = self.client_socket.recv(5120) # bufSize 1KB->5KB
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
                    "result": model.result
                }
                results.append(result)

            print("INFO: {} - Results analyzed is \"{}\"".format(datetime.now(), results))

            self.client_socket.sendall("INFO: {} - Successfully received".format(datetime.now()).encode())

    def shutdown_server(self):
        self.client_socket.close()
        self.server_socket.close()