import datetime
import socket
import os
import json

from utils import Logging


class Communicator:
    def __init__(self, communication_info, streaming_url, message_pool):
        self.client_socket = None
        self.message_pull = None
        self.host = communication_info["server_url"]["ip"]
        self.port = communication_info["server_url"]["port"]
        self.streaming_url = streaming_url
        self.message_size = communication_info["message_size"]
        self.message_pool = message_pool
        self.load_client()


    def load_client(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.client_socket.sendall(str({
            "id": self.streaming_url,
            "message_type": "init",
            "time": str(datetime.datetime.now())
        }).encode())
        received_data = self.client_socket.recv(self.message_size)
        print(Logging.d((received_data.decode())))
        self.client_socket.close()


    def run(self):
        print("test")


    def send_event(self, event_name, event_time, event_type, message):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.client_socket.send(str({
                "id": self.streaming_url,
                "event_name": event_name,
                "message_type": event_type,
                "event_time": str(event_time),
                "message": message
            }).encode())
            received_data = self.client_socket.recv(self.message_size)
            print(Logging.d((received_data.decode())))
            self.client_socket.close()
        except:
            print(Logging.e("Failed to send message"))

    def __delete__(self, instance):
        self.client_socket.close()

    # def send_sequence(self, event_name, event_time, event_type):
    #     print("test")
    #     server_addr = (self.communication_info["server_url"]["ip"], self.communication_info["server_url"]["port"])
    #     message_size = self.communication_info["message_size"]
    #     message = {
    #         "event_name": event_name,
    #         "time": event_time,
    #         "event_type": event_type
    #     }
    #
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    #         client_socket.connect(server_addr)
    #         client_socket.send('{}'.format(str(message)).encode())
    #         received_message = client_socket.recv(message_size)
    #         print(Logging.i("received from server: {}".format(received_message)))
