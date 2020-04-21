from Modules.dummy.main import Dummy
from Modules.dummy2.main import Dummy2
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

        dummy_model = Dummy()
        dummy2_model = Dummy2()

        self.models.append(dummy_model)
        self.models.append(dummy2_model)

    def run_server(self):
        self.client_socket, self.addr = self.server_socket.accept()
        print("INFO: {} - Connected by {}".format(datetime.now(), self.addr))
        while True:
            data = self.client_socket.recv(1024)
            if not data:
                break
            json_data = ast.literal_eval(str(data))
            print("INFO: {} - Received from {}\t".format(datetime.now(), self.addr))

            threads = []
            for model in self.models:
                thread = Thread(target=model.inference_by_path, args=(json_data,))
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