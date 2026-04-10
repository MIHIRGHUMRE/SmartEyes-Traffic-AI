import cv2
import time

class VideoProcessor:
    def __init__(self, source):
        """
        Initialize video capture.
        :param source: Can be 0 for webcam, or a path to a video file.
        """
        self.source = source
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise ValueError(f"Unable to open video source: {source}")

    def get_frame(self):
        """
        Reads a frame from the video source.
        :return: (success (bool), frame (numpy array))
        """
        success, frame = self.cap.read()
        return success, frame

    def is_image_clear(self, frame, threshold=100.0):
        """
        Check image clarity using Laplacian variance (blur detection).
        :param frame: Image frame
        :param threshold: Variance threshold below which image is considered blurry.
        :return: Boolean indicating if image is clear.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return variance > threshold

    def release(self):
        self.cap.release()
