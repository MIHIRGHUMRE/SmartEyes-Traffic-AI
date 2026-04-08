import cv2
import requests
from typing import Optional, Union
import os
from pathlib import Path

class MediaCapture:
    """Handles camera feed, video files, and citizen uploads."""

    def __init__(self, source: Union[str, int] = 0):
        """
        Initialize media capture.

        Args:
            source: Camera index (int) or video file path (str)
        """
        self.source = source
        self.cap = None

    def start_capture(self) -> bool:
        """Start capturing from the specified source."""
        if isinstance(self.source, str) and os.path.isfile(self.source):
            self.cap = cv2.VideoCapture(self.source)
        else:
            self.cap = cv2.VideoCapture(self.source)

        return self.cap.isOpened()

    def get_frame(self) -> Optional[object]:
        """Get a single frame from the capture source."""
        if self.cap is None or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if ret:
            return frame
        return None

    def stop_capture(self):
        """Stop the capture and release resources."""
        if self.cap:
            self.cap.release()

    @staticmethod
    def upload_from_citizen(file_path: str, api_endpoint: str, user_id: str) -> dict:
        """Handle citizen upload to cloud."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'user_id': user_id}
            response = requests.post(api_endpoint, files=files, data=data)
            return response.json()

    def __del__(self):
        self.stop_capture()