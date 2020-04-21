import socket
import os
import json
import time
import sys
import argparse

class RequestClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def send_od_result(self, od_result):
        self.client_socket.sendall(str(od_result).encode())
        data = self.client_socket.recv(1024)
        print("Received", repr(data.decode()))

    def load_jsonfile(self, od_result_file_path=os.path.join(os.getcwd(), "data", "json", "sample1.json")):
        with open(od_result_file_path) as od_result_file:
            od_result = json.load(od_result_file)
            return od_result

    def end_client(self):
        self.client_socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Please check that you enter parameters and server is turned on")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="Server ip")
    parser.add_argument("--port", type=int, default=10001, help="Server port")
    parser.add_argument("--json_dir", type=str, default=os.path.join(os.getcwd(), "data", "json"), help="Json file directory path")

    try:
        opt = parser.parse_known_args()[0]

        request_client = RequestClient(opt.ip, opt.port)
        dir_path = opt.json_dir

        for json_file in os.listdir(dir_path):
            json_path = os.path.join(dir_path, json_file)
            print("INFO: Send json data({})".format(json_path))
            od_result = request_client.load_jsonfile(json_path)
            request_client.send_od_result(od_result)

        request_client.end_client()

    except:
        print("")
        parser.print_help()
        sys.exit(0)