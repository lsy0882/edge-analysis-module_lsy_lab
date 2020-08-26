import jetson.inference
import jetson.utils
import cv2
import numpy as np
import imutils
import time

class JIDetector:
    def __init__(self, model_name):
        self.net = jetson.inference.detectNet(model_name)
        self.model_name = model_name
        self.classes = [
            "__background__","person","bicycle","car","motorcycle","airplane","bus",
            "train","truck","boat","traffci light","fire hydrant","","stop sign",
            "parking meter","bench","bird","cat","dog","horse","sheep","cow","elephant",
            "bear","zebra","giraffe","","backpack","umbrella","","","handbag","tie",
            "suitcase","frisbee","skis","snowboard","sprotsball","kite","baseball bat",
            "baseball glove", "skateboard","surfboard","tennis racket","bottle","",
            "wine glass", "cup","fork","knife","spoon","bowl","banana","apple","sandwich",
            "oragne","broccoli","corrot","got dog","pizza","donut","cake","chair","couch",
            "potted plant","bed","","dining table","","","toilet","","tv","laptop","mouse",
            "remote","keyboard","cellphone","microwave","oven", "toaster","sink","refrigerator",
            "","book","clock","vase","scissors","teddy bear", "hair drier","toothbrush"
        ]

    def inference(self, frame):
        results = []
        try :
            frame = imutils.resize(frame, width=640, height=360)
            frame_cuda = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA).astype(np.float32)
            frame_cuda = jetson.utils.cudaFromNumpy(frame_cuda)
            predictions = self.net.Detect(frame_cuda, frame.shape[1], frame.shape[0])

            for prediction in predictions:
                label = self.classes[prediction.ClassID]
                score = float(prediction.Confidence * 100)
                x = int(prediction.Left)
                y = int(prediction.Top)
                width = int(prediction.Width)
                height = int(prediction.Height)
                result = {
                    "label": [
                        {"description": label, "score": score,}
                    ],
                    "position" : {
                        "x": x,
                        "y": y,
                        "w": width,
                        "h": height
                    }
                }
                results.append(result)
        except :
            print(type(frame))
        return results

    def detect(self, frame_info):
        start = time.time()
        results = self.inference(frame_info["frame"])
        end = time.time()

        detection_result = {
            "image_path": "%06d.jpg"%(frame_info["frame_num"]),
            "modules": self.model_name,
            "frame_num": frame_info["frame_num"],
            "analysis_time": end - start,
            "cam_id": 0,
            "results": []
        }

        detection_result["results"].append({"detection_result": []})
        for result in results:
            detection_result["results"][0]["detection_result"].append(result)

        return detection_result