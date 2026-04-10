from ultralytics import YOLO
import os
import torch

_original_load = torch.load
def _safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _safe_load

class YoloDetector:
    def __init__(self, model_path="yolov8n.pt", conf_threshold=0.5):
        """
        Initializes the YOLO model.
        In production, model_path should point to 'models/best.pt'
        """
        self.conf_threshold = conf_threshold
        # If the specific model doesn't exist, fallback to generic yolov8n to prevent crash during testing
        if not os.path.exists(model_path):
            print(f"Warning: {model_path} not found. Falling back to generic 'yolov8n.pt'")
            self.model = YOLO("yolov8n.pt")
        else:
            self.model = YOLO(model_path)

    def detect(self, frame):
        """
        Run inference on a single frame.
        :param frame: Image array
        :return: List of detected objects with class name, confidence, and bounding box.
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        detected_objects = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Class ID
                cls_id = int(box.cls[0].item())
                # Class Name
                cls_name = self.model.names[cls_id]
                # Confidence
                conf = float(box.conf[0].item())
                # Bounding box coords [x1, y1, x2, y2]
                xyxy = box.xyxy[0].tolist()
                
                detected_objects.append({
                    "class": cls_name,
                    "confidence": conf,
                    "bbox": xyxy
                })
        
        # Optionally overlay boxes on frame for visual debug
        annotated_frame = results[0].plot()
        return detected_objects, annotated_frame
