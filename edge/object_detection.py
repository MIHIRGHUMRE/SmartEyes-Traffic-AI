from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Tuple
import torch

class ObjectDetector:
    """YOLO-based object detection for traffic violations."""

    def __init__(self, model_path: str = 'models/yolov8n.pt', conf_threshold: float = 0.5):
        """
        Initialize YOLO object detector.

        Args:
            model_path: Path to YOLO model weights
            conf_threshold: Confidence threshold for detections
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

        # Traffic-related classes (COCO dataset indices)
        self.traffic_classes = {
            2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck',
            1: 'bicycle', 0: 'person'
        }

    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect objects in frame.

        Returns:
            List of detections with bbox, confidence, class
        """
        results = self.model(frame, conf=self.conf_threshold)

        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())

                if cls in self.traffic_classes:
                    detections.append({
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': float(conf),
                        'class': self.traffic_classes[cls],
                        'class_id': cls
                    })

        return detections

    def detect_batch(self, frames: List[np.ndarray]) -> List[List[Dict]]:
        """Detect objects in batch of frames."""
        return [self.detect(frame) for frame in frames]

    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw bounding boxes on frame."""
        img = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            label = f"{det['class']} {det['confidence']:.2f}"

            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return img