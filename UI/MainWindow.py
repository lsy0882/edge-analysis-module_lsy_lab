import os, json
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from UI.VideoViewer import VideoViewer
from Worker.VideoWorker import VideoWorker
from UI.SettingsWindow import SettingsWindow
from Worker.DetectorWorker import DetectorWorker

form_class = uic.loadUiType("UI/MainWindow.ui")[0]

class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.table_row_count_list = []

        self.video_viewer = VideoViewer()
        self.video_worker = VideoWorker()
        self.detector_worker = DetectorWorker(self.video_worker, parent=self)
        self.vertical_layout_video_viewer.addWidget(self.video_viewer)

        self.button_start.clicked.connect(self.event_start)
        self.button_ready.clicked.connect(self.event_ready)
        self.button_server_url_test.clicked.connect(self.event_detection_start)
        self.button_settings.clicked.connect(self.event_settings)
        self.detector_worker.table_widget_add_row_signal.connect(self.add_row)
        self.detector_worker.edit_text_log_signal.connect(self.add_log)

        table_header_objects = ['frame number', 'timestamp', 'detection results']
        font = QFont()
        font.setPointSize(10)

        self.table_widget_list = []

        label_list = []
        label_name_list = [
            "Object Detection 결과",
            "폭행(assault) 이벤트 검출",
            "배회자(wanderer) 이벤트 검출",
            "위험요소(obstacle) 이벤트 검출",
            "납치(kidnapping) 이벤트 검출",
            "미행(tailing) 이벤트 검출",
            "Re-id 이벤트"]

        for i in range(len(label_name_list)) :
            self.table_row_count_list.append(0)
            label_list.append(QLabel(self))

        for label, label_name in zip(label_list, label_name_list):
            label.setText(label_name)


        self.table_widget_object_detction = QTableWidget(self)
        self.table_widget_assault = QTableWidget(self)
        self.table_widget_wanderer = QTableWidget(self)
        self.table_widget_obstacle = QTableWidget(self)
        self.table_widget_tailing = QTableWidget(self)
        self.table_widget_kidnapping = QTableWidget(self)
        self.table_widget_reid = QTableWidget(self)
        self.table_widget_list.append(self.table_widget_object_detction)
        self.table_widget_list.append(self.table_widget_assault)
        self.table_widget_list.append(self.table_widget_wanderer)
        self.table_widget_list.append(self.table_widget_obstacle)
        self.table_widget_list.append(self.table_widget_tailing)
        self.table_widget_list.append(self.table_widget_kidnapping)
        self.table_widget_list.append(self.table_widget_reid)

        for table_widget in self.table_widget_list:
            table_widget.setColumnCount(len(table_header_objects))
            table_widget.setHorizontalHeaderLabels(table_header_objects)
            table_widget_header = table_widget.horizontalHeader()
            for column in range(0, len(table_header_objects)):
                table_widget_header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            table_widget.setFont(font)


        for label, table_widget in zip(label_list, self.table_widget_list):
            self.vertical_layout_monitoring.addWidget(label)
            self.vertical_layout_monitoring.addWidget(table_widget)


        self.setting_window = SettingsWindow()
        self.video_thread = QtCore.QThread()

        self.button_ready.setEnabled(False)
        self.button_start.setEnabled(False)

    def event_settings(self):
        self.button_ready.setEnabled(True)
        self.setting_window.show()

    def event_ready(self):
        settings_attr = json.load(open(os.path.join(os.getcwd(), "settings", "settings.json")))
        self.video_worker.set_attribute(
            video_url=settings_attr["video_url"],
            extract_fps=settings_attr["extract_fps"],
            display_fps=settings_attr["display_fps"]
        )
        self.video_thread.start()
        self.video_worker.moveToThread(self.video_thread)
        self.video_worker.video_signal_frame.connect(self.video_viewer.setImage)
        self.add_row_type = settings_attr["add_row_type"]

        self.detector_worker.connect_button_start(self.button_start)
        self.detector_worker.start()

    def event_start(self):
        self.add_log("VERBOSE:\tAnalysis Start")

        self.video_worker.event_start()
        self.button_start.setEnabled(False)
        self.button_settings.setEnabled(False)
        self.button_server_url_test.setEnabled(False)
        self.button_ready.setEnabled(False)

    def event_detection_start(self):
        self.detector_object.event_detection_start()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.video_worker.event_stop()
        del self.video_worker
        del self.video_thread

    @QtCore.pyqtSlot(int, int, int, str)
    def add_row(self, index, row, column, text):
        if self.add_row_type == "one_line":
            row = 0
        if column == 0:
            self.table_row_count_list[index] = 1
        elif column != 0 and self.add_row_type != "one_line":
            self.table_row_count_list[index] += 1
        self.table_widget_list[index].setRowCount(self.table_row_count_list[index])
        item = self.table_widget_list[index].item(row, column)
        if item:
            item.setText(text)
        else:
            item = QTableWidgetItem(text)
            self.table_widget_list[index].setItem(row, column, item)
            self.table_widget_list[index].selectRow(row)

    @QtCore.pyqtSlot(str)
    def add_log(self, text):
        self.edit_text_log.appendPlainText(text)