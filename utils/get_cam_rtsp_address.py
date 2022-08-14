from config import config
from utils.setting_utils import load_settings

settings = load_settings(config.SETTINGS_PATH)
rtsp_url = settings["settings"]["cctv_info"]["streaming_url"]
print(rtsp_url)