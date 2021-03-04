import socket
import os
import json

from utils import Logging


class Communicator:
    def __init__(self):
        self.server_address = ""
        self.client_socket = None
        self.detection_result_pool = None

    def load_client(self, server_address, cam_address, detection_result_pool):
        print(server_address, cam_address)
        self.detection_result_pool = detection_result_pool
        host, port = server_address.split(":")
        if host is "":
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 0))
            self.host = str(s.getsockname()[0])
        else :
            self.host = host
        self.port = int(port)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.client_socket.sendall(str({"message_type": "init", "edge_type": "single", "cam_address": cam_address.split(",")}).encode())
        return True, Logging.i("Server is successfully loaded - {}:{}".format(self.host, self.port))

    def run(self):
        print("test")

    def send_detection_result(self, detection_result):
        self.client_socket.sendall(str({"message_type": "result", "detection_result": detection_result}).encode())

    def __delete__(self, instance):
        self.client_socket.close()