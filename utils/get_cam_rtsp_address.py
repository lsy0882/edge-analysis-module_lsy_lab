import sys
sys.path.append("/media/nvidia/external/edge-analysis-module")

from config import config
from utils.params_util import load_settings

settings = load_settings(config.SETTINGS_PATH)
rtsp_url = settings["settings"]["cctv_info"]["streaming_url"]
print(rtsp_url)
