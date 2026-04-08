import cv2
import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict

class ObjectTracker:
    """Track objects across frames using SORT or DeepSORT."""

    def __init__(self, max_age: int = 30, min_hits: int = 3):
        """
        Initialize object tracker.

        Args:
            max_age: Maximum frames to keep track alive
            min_hits: Minimum hits to confirm track
        """
        self.tracker = cv2.TrackerCSRT_create()  # Using CSRT for simplicity
        self.trackers = []
        self.tracks = defaultdict(list)
        self.track_id = 0
        self.max_age = max_age
        self.min_hits = min_hits

    def update(self, frame: np.ndarray, detections: List[Dict]) -> List[Dict]:
        """
        Update tracks with new detections.

        Returns:
            List of tracked objects with IDs
        """
        tracked_objects = []

        # Update existing trackers
        to_delete = []
        for i, tracker_info in enumerate(self.trackers):
            success, bbox = tracker_info['tracker'].update(frame)
            if success:
                tracked_objects.append({
                    'id': tracker_info['id'],
                    'bbox': list(bbox),
                    'class': tracker_info['class'],
                    'age': tracker_info['age'] + 1
                })
                tracker_info['age'] += 1
            else:
                to_delete.append(i)

        # Remove failed trackers
        for i in reversed(to_delete):
            del self.trackers[i]

        # Associate detections with tracks (simple IoU-based)
        for det in detections:
            best_iou = 0.5
            best_track = None

            for obj in tracked_objects:
                iou = self._calculate_iou(det['bbox'], obj['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_track = obj

            if best_track:
                # Update existing track
                best_track['bbox'] = det['bbox']
                best_track['class'] = det['class']
                best_track['age'] = 0
            else:
                # Create new track
                self.track_id += 1
                tracked_objects.append({
                    'id': self.track_id,
                    'bbox': det['bbox'],
                    'class': det['class'],
                    'age': 0
                })

        # Remove old tracks
        tracked_objects = [obj for obj in tracked_objects if obj['age'] < self.max_age]

        return tracked_objects

    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate Intersection over Union of two bounding boxes."""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2

        # Intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0

        intersection = (x2_i - x1_i) * (y2_i - y1_i)

        # Union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0