import cv2
import numpy as np
from typing import List, Optional
import time

class FrameExtractor:
    """Extract frames from video feed for processing."""

    def __init__(self, fps: int = 30, quality_threshold: float = 0.7):
        """
        Initialize frame extractor.

        Args:
            fps: Target frames per second to process
            quality_threshold: Minimum quality score for frame acceptance
        """
        self.fps = fps
        self.quality_threshold = quality_threshold
        self.last_frame_time = 0

    def extract_frames(self, video_path: str) -> List[np.ndarray]:
        """Extract frames from video file."""
        cap = cv2.VideoCapture(video_path)
        frames = []

        if not cap.isOpened():
            return frames

        frame_interval = 1.0 / self.fps

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            current_time = time.time()
            if current_time - self.last_frame_time >= frame_interval:
                if self._assess_quality(frame):
                    frames.append(frame)
                self.last_frame_time = current_time

        cap.release()
        return frames

    def extract_frame_from_stream(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Extract single frame from live stream."""
        current_time = time.time()
        if current_time - self.last_frame_time >= 1.0 / self.fps:
            if self._assess_quality(frame):
                self.last_frame_time = current_time
                return frame
        return None

    def _assess_quality(self, frame: np.ndarray) -> bool:
        """Assess image quality using Laplacian variance."""
        if frame is None:
            return False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Normalize variance to 0-1 scale (rough approximation)
        quality_score = min(variance / 500.0, 1.0)

        return quality_score >= self.quality_threshold