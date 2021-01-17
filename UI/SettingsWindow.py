import os, json
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui, QtCore

form_class = uic.loadUiType("UI/SettingsWindow.ui")[0]

class SettingsWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.video_url = ""
        self.server_url = ""
        self.extract_fps = ""
        self.dataset = ""
        self.model = ""

        self.load_settings()

        # Set line edits only number
        self.edit_text_fps.setValidator(QtGui.QIntValidator(0, 30))
        self.edit_text_server_port.setValidator(QtGui.QIntValidator(0, 99999))

        # Set button events
        self.button_open.clicked.connect(self.event_button_open)
        self.button_server_url_test.clicked.connect(self.event_button_server_url_test)
        self.button_ok.clicked.connect(self.event_button_ok)
        self.button_cancel.clicked.connect(self.event_button_cancel)

    def event_button_open(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '.', "Video Files (*.mp4 *.flv *.ts *.mts *.avi)")
        self.edit_text_video_url.setText(fname[0])

    def event_button_server_url_test(self):
        print("server url test")

    def event_button_ok(self):
        self.save_settings()
        self.close()

    def event_button_cancel(self):
        self.close()


    def load_settings(self):
        self.settings_dir = os.path.join(os.getcwd(), "settings")
        setting_json_file = open(os.path.join(self.settings_dir, "settings.json"))
        settings = json.load(setting_json_file)
        setting_json_file.close()

        combo_box_json_file = open(os.path.join(self.settings_dir, "combo_box.json"))
        combo_box_items = json.load(combo_box_json_file)
        combo_box_json_file.close()

        self.combo_box_dataset.addItems(combo_box_items["dataset"])
        self.combo_box_model.addItems(combo_box_items["model"])

        self.edit_text_video_url.setText(settings["video_url"]),
        self.edit_text_server_url.setText(settings["server_url"]),
        self.edit_text_server_port.setText(str(settings["server_port"])),
        self.edit_text_fps.setText(str(settings["extract_fps"])),
        self.combo_box_dataset.setCurrentIndex(settings["dataset"])
        self.combo_box_model.setCurrentIndex(settings["model"])
        self.check_box_analysis_type.setChecked(settings["analysis_type"])

    def save_settings(self):
        settings = {
            "video_url": self.edit_text_video_url.text(),
            "server_url": self.edit_text_server_url.text(),
            "server_port": int(self.edit_text_server_port.text()),
            "extract_fps": self.edit_text_fps.text(),
            "dataset": int(self.combo_box_dataset.currentIndex()),
            "model": int(self.combo_box_model.currentIndex()),
            "analysis_type": self.check_box_analysis_type.isChecked()
        }

        with open(os.path.join(self.settings_dir, "settings.json"), 'w') as settings_json:
            json.dump(settings, settings_json, indent=4)
            settings_json.close()

