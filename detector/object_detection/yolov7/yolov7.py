import tensorrt as trt
import pycuda.autoinit
import pycuda.driver as cuda
import numpy as np
import os
import cv2

from detector.object_detection.template.ObjectDetection import ObjectDetection
from config import dataset
from config import config
from detector.object_detection.yolov7.utility.yolov7 import preproc, multiclass_nms


class TRTyolov7(ObjectDetection):
    def __init__(self, model='yolov7-trt', model_dataset='obstacle-15', score_threshold=0.1, nms_threshold=0.5):
        super().__init__(model)
        self.imgsz = (640, 640)
        self.mean = None
        self.std = None
        self.class_names = dataset.OBJECT_DATASET_CLASSES[model_dataset]
        self.n_classes = len(self.class_names)

        logger = trt.Logger(trt.Logger.WARNING)
        runtime = trt.Runtime(logger)
        trt.init_libnvinfer_plugins(logger, '')  # initialize TensorRT plugins
        with open("detector/object_detection/yolov7/weights/yolov7-obstacle-single.trt", "rb") as f:
            serialized_engine = f.read()
        engine = runtime.deserialize_cuda_engine(serialized_engine)
        self.context = engine.create_execution_context()
        self.inputs, self.outputs, self.bindings = [], [], []
        self.stream = cuda.Stream()
        for binding in engine:
            size = trt.volume(engine.get_binding_shape(binding))
            dtype = trt.nptype(engine.get_binding_dtype(binding))
            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            self.bindings.append(int(device_mem))
            if engine.binding_is_input(binding):
                self.inputs.append({'host': host_mem, 'device': device_mem})
            else:
                self.outputs.append({'host': host_mem, 'device': device_mem})

    @staticmethod
    def postprocess(predictions, ratio):
        boxes = predictions[:, :4]
        scores = predictions[:, 4:5] * predictions[:, 5:]
        boxes_xyxy = np.ones_like(boxes)
        boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2.
        boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2.
        boxes_xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2.
        boxes_xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2.
        boxes_xyxy /= ratio
        dets = multiclass_nms(boxes_xyxy, scores, nms_thr=0.45, score_thr=0.1)
        return dets

    def infer(self, img):
        self.inputs[0]['host'] = np.ravel(img)
        for inp in self.inputs:
            cuda.memcpy_htod_async(inp['device'], inp['host'], self.stream)
        self.context.execute_async_v2(
            bindings=self.bindings,
            stream_handle=self.stream.handle)
        for out in self.outputs:
            cuda.memcpy_dtoh_async(out['host'], out['device'], self.stream)
        self.stream.synchronize()

        data = [out['host'] for out in self.outputs]
        return data

    def inference_image(self, image, confidence_threshold=0.1):
        img, ratio = preproc(image, self.imgsz, self.mean, self.std)
        data = self.infer(img)
        num, final_boxes, final_scores, final_cls_inds = data
        final_boxes = np.reshape(final_boxes / ratio, (-1, 4))
        dets = np.concatenate([final_boxes[:num[0]], np.array(final_scores)[:num[0]].reshape(-1, 1),
                               np.array(final_cls_inds)[:num[0]].reshape(-1, 1)], axis=-1)
        results = []
        if dets is not None:
            boxes, scores, cls_idxs = dets[:, :4], dets[:, 4], dets[:, 5]
            for i in range(len(boxes)):
                cls_idx = int(cls_idxs[i])
                score = float(scores[i])
                box = boxes[i]
                x = int(box[0])
                y = int(box[1])
                w = int(box[2]) - x
                h = int(box[3]) - y

                results.append({
                    "label": [{
                        "description": self.class_names[cls_idx],
                        "score": score,
                        "class_idx": cls_idx
                    }],
                    "position": {
                        "x": x,
                        "y": y,
                        "w": w,
                        "h": h
                    }
                })
        return results

    def inference_image_batch(self, images):
        """
        :param image: input images(list in dict: [np array(cv2 image)])
        :return: detection results(bounding box(x1, y1, x2, y2), score, class, class index) of each images
            - format:
                [[{"label": {"class": cls, "score": score, "class_idx": cls_idx},
                 "position": {"x": x, "y": y, "w": w, "h": h}}, ...], ...]
        """
        results = []

        for i, image in enumerate(images):
            results.append(self.inference_image(image))

        self.results = results

        return results