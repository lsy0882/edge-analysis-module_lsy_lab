from utils.yolo_with_plugins import TrtYOLO
from utils.yolo_classes import get_cls_dict
from utils import PrintLog

class YOLOv4:
    def __init__(self, frame_info_pool=None, detection_result_pool=None, final_result_pool=None, model='yolov4-416', dataset='obstacle'):
        """
        :param model: model name
        :param category_num:
        """
        self.results = dict()
        self.model_name = model
        self.dataset = dataset
        self.frame_info_pool = frame_info_pool
        self.detection_result_pool = detection_result_pool
        self.final_result_pool = final_result_pool
        if dataset == "coco":
            category_num = 80
        else :
            category_num = 15
        self.cls_dict = get_cls_dict(category_num)

        yolo_dim = model.split('-')[-1]
        if 'x' in yolo_dim:
            dim_split = yolo_dim.split('x')
            if len(dim_split) != 2:
                raise SystemExit('ERROR: bad yolo_dim (%s)!' % yolo_dim)
            w, h = int(dim_split[0]), int(dim_split[1])
        else:
            h = w = int(yolo_dim)
        if h % 32 != 0 or w % 32 != 0:
            raise SystemExit('ERROR: bad yolo_dim (%s)!' % yolo_dim)

        self.model = TrtYOLO(model, (h, w), category_num)

        PrintLog.i("Object detection model is loaded - {}\t{}".format(model, dataset))

    def inference_by_image(self, image, confidence_threshold=0.1):
        """
        :param image: input image
        :param confidence_threshold: confidence/score threshold for object detection.
        :return: bounding box(x1, y1, x2, y2), scores, classes
        """
        boxes, scores, classes = self.model.detect(image, confidence_threshold)
        results = []
        for box, score, cls in zip(boxes, scores, classes):
            results.append({
                "label" :[
                    {
                        "description": self.cls_dict.get(int(cls), 'CLS{}'.format(int(cls))),
                        "score": float(score),
                        "class_idx": int(cls)
                    }
                ],
                "position": {
                    "x": int(box[0]),
                    "y": int(box[1]),
                    "w": int(box[2] - box[0]),
                    "h": int(box[3] - box[1])
                }
            })

        return results

    def run(self):
        PrintLog.i("Frame Number\tTimestamp")
        while True:
            if len(self.frame_info_pool) > 0:
                frame_info = self.frame_info_pool.pop(0)
                result = self.inference_by_image(frame_info["frame"])
                detection_result = dict()
                detection_result["cam_address"] = frame_info["cam_address"]
                detection_result["timestamp"] = frame_info["timestamp"]
                detection_result["frame_number"] = frame_info["frame_number"]
                detection_result["results"] = []
                detection_result["results"].append({"detection_result": result})
                self.detection_result_pool.append(detection_result)
                # PrintLog.i("{}\t{}\t{}\t{}".format(detection_result["frame_number"], len(self.frame_info_pool), len(self.detection_result_pool), len(self.final_result_pool)))
