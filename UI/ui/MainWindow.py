import os, json
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from ui.ui.VideoViewer import VideoViewer
from ui.ui.SettingsWindow import SettingsWindow
from ui.worker.VideoWorker import VideoWorker
from ui.worker.DetectorWorker import DetectorWorker
from ui.worker.SendMessageWorker import SendMessageWorker
from communicator.Socket import Communicator

form_class = uic.loadUiType("ui/ui/MainWindow.ui")[0]

class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.table_row_count_list = []
        self.table_row_multiple = False
        self.communicator = None
        self.video_viewer = VideoViewer()
        self.video_worker = VideoWorker()
        self.send_message_worker = SendMessageWorker(self.video_worker, parent=self)
        self.detector_worker = DetectorWorker(self.video_worker, self.send_message_worker, parent=self)
        self.vertical_layout_video_viewer.addWidget(self.video_viewer)

        self.button_start.clicked.connect(self.event_start)
        self.button_ready.clicked.connect(self.event_ready)
        self.check_box_send_message.clicked.connect(self.event_send_message)
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
        self.check_box_send_message.setEnabled(False)

    def event_settings(self):
        self.button_ready.setEnabled(True)
        self.setting_window.show()

    def event_ready(self):
        self.communicator = Communicator()
        ret, log = self.communicator.load_client()
        self.add_log(log)

        settings_attr = json.load(open(os.path.join(os.getcwd(), "settings", "settings.json")))
        self.video_worker.set_attribute(settings_attr=settings_attr)
        self.video_thread.start()
        self.video_worker.moveToThread(self.video_thread)
        self.video_worker.video_signal_frame.connect(self.video_viewer.setImage)
        self.table_row_multiple = settings_attr["table_row_multiple"]
        self.button_settings.setEnabled(False)
        self.check_box_send_message.setEnabled(True)

        self.detector_worker.connect_button_start(self.button_start)
        self.detector_worker.start()


    def event_start(self):
        self.add_log("VERBOSE:\tAnalysis Start")
        self.button_start.setEnabled(False)
        self.button_ready.setEnabled(False)

        self.video_worker.event_start()

    def event_detection_start(self):
        self.detector_object.event_detection_start()

    def event_send_message(self):
        if not self.send_message_worker.get_start_state():
            self.send_message_worker.start()
            self.send_message_worker.resume_worker()
        else :
            if self.check_box_send_message.isChecked():
                self.send_message_worker.resume_worker()
                self.add_log("VERBOSE: Message worker is resumed")
            else :
                self.send_message_worker.pause_worker()
                self.add_log("VERBOSE: Message worker is paused")

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.video_worker.event_stop()
        del self.video_thread
        del self.video_worker
        del self.detector_worker
        del self.send_message_worker

    @QtCore.pyqtSlot(int, int, int, str)
    def add_row(self, index, row, column, text):
        if not self.table_row_multiple:
            row = 0
            self.table_row_count_list[index] = 1
            self.table_widget_list[index].setRowCount(self.table_row_count_list[index])

        elif self.table_row_multiple:
            if column == 0:
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
