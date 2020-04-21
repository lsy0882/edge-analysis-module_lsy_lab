from Modules.dummy.main import Dummy
from Modules.dummy2.main import Dummy2
from threading import Lock, Thread
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


    def run_server(self):
        self.client_socket, self.addr = self.server_socket.accept()
        print("INFO: {} - Connected by {}".format(datetime.now(), self.addr))
        while True:
            data = self.client_socket.recv(1024)
            if not data:
                break
            json_data = ast.literal_eval(str(data))
            print("INFO: {} - Received from {}\t".format(datetime.now(), self.addr))


            results = []


            print("INFO: {} - Results analyzed is \"{}\"".format(datetime.now(), results))

            self.client_socket.sendall("INFO: {} - Successfully received".format(datetime.now()).encode())

    def shutdown_server(self):
        self.client_socket.close()
        self.server_socket.close()