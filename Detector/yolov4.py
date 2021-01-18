from utils.yolo_with_plugins import TrtYOLO
from utils.yolo_classes import get_cls_dict

class YOLOv4:
    def __init__(self, model='yolov4-416', dataset='coco',category_num=15):
        """
        :param model: model name
        :param category_num:
        """
        self.results = dict()
        self.model_name = model
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