import argparse
import sys
from ui.ui.MainWindow import MainWindow
from console.MainConsole import MainConsole

from PyQt5 import QtWidgets


def main_ui():
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())


def main_cons(server_address, cam_address, analysis_fps, dataset, model):
    import pycuda.autoinit
    main_console = MainConsole(server_address, cam_address, analysis_fps, dataset, model)
    ret = main_console.init()
    if ret:
        main_console.run()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Please check that you enter parameters and server is turned on.")
    parser.add_argument("--mode", type=str, default="ui", required=True, help="Please input mode(console or ui).")
    parser.add_argument("--server_address", type=str, default="", help="Please input server address. (e.g. 192.168.0.100:8000")
    parser.add_argument("--cam_address", type=str, default="", help="Please input camera url(s). (e.g. rtsp://192.168.0.10/1_360p,rtsp://192.168.0.10/2_360p...")
    parser.add_argument("--analysis_fps", type=int, default=4, help="Please input fps to be analyzed.")
    parser.add_argument("--model", type=str, default="yolov4-416", help="Plase input model of object detector.(e.g. yolov3-416, yolov4-416)")
    parser.add_argument("--dataset", type=str, default="obstacle", help="Please input dataset of object detector.(e.g. mscoco, obstacle)")

    option = parser.parse_known_args()[0]
    mode = str(option.mode)

    if mode == "console":
        server_address = str(option.server_address)
        cam_address = str(option.cam_address)
        analysis_fps = int(option.analysis_fps)
        model = str(option.model)
        dataset = str(option.dataset)
        if cam_address == "":
            parser.print_help()
            sys.exit(0)
        else :
            main_cons(cam_address, server_address, analysis_fps, model, dataset)
    else :
        main_ui()

