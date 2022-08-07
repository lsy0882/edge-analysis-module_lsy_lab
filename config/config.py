from detector.object_detection.yolov4.yolov4 import YOLOv4
from detector.tracker.byte_tracker.BYTETracker import BYTETracker
from detector.tracker.sort.Sort import Sort
from detector.event.assault.main import AssaultEvent
from detector.event.falldown.main import FalldownEvent
from detector.event.kidnapping.main import KidnappingEvent
from detector.event.tailing.main import TailingEvent
from detector.event.wanderer.main import WandererEvent


DEBUG = True
SETTINGS_PATH = "config/settings.yml"

OBJECT_MODEL = {
    "yolov4-416": YOLOv4
}
TRACKER = {
    "byte_tracker": BYTETracker,
    "sort_tracker": Sort
}
EVENT_MODEL = {
    "assault": AssaultEvent,
    "falldown": FalldownEvent,
    "kidnapping": KidnappingEvent,
    "tailing": TailingEvent,
    "wanderer": WandererEvent,
}