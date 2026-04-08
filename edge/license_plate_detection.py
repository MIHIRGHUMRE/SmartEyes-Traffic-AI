import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import re

class LicensePlateDetector:
    """Detect and extract license plates from vehicle images."""

    def __init__(self, min_area: int = 500, max_area: int = 10000):
        """
        Initialize license plate detector.

        Args:
            min_area: Minimum area for plate detection
            max_area: Maximum area for plate detection
        """
        self.min_area = min_area
        self.max_area = max_area

    def detect_plates(self, frame: np.ndarray, detections: List[Dict]) -> List[Dict]:
        """
        Detect license plates in vehicles.

        Args:
            frame: Input image
            detections: Vehicle detections from YOLO

        Returns:
            List of license plate detections
        """
        plates = []

        for det in detections:
            if det['class'] in ['car', 'motorcycle', 'truck', 'bus']:
                plate = self._extract_plate(frame, det['bbox'])
                if plate:
                    plates.append({
                        'vehicle_bbox': det['bbox'],
                        'plate_bbox': plate['bbox'],
                        'plate_image': plate['image'],
                        'confidence': plate['confidence']
                    })

        return plates

    def _extract_plate(self, frame: np.ndarray, vehicle_bbox: List[float]) -> Optional[Dict]:
        """Extract license plate from vehicle region."""
        x1, y1, x2, y2 = map(int, vehicle_bbox)
        vehicle_roi = frame[y1:y2, x1:x2]

        if vehicle_roi.size == 0:
            return None

        # Convert to grayscale
        gray = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2GRAY)

        # Apply bilateral filter to reduce noise
        gray = cv2.bilateralFilter(gray, 11, 17, 17)

        # Edge detection
        edged = cv2.Canny(gray, 30, 200)

        # Find contours
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        plate_contour = None
        for contour in contours:
            # Approximate contour
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.018 * peri, True)

            # Check if contour has 4 corners (rectangle)
            if len(approx) == 4:
                # Check area
                area = cv2.contourArea(contour)
                if self.min_area < area < self.max_area:
                    plate_contour = approx
                    break

        if plate_contour is not None:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(plate_contour)
            plate_image = vehicle_roi[y:y+h, x:x+w]

            # Calculate confidence based on aspect ratio
            aspect_ratio = w / float(h)
            confidence = 1.0 if 2.0 < aspect_ratio < 6.0 else 0.5

            return {
                'bbox': [x1 + x, y1 + y, x1 + x + w, y1 + y + h],
                'image': plate_image,
                'confidence': confidence
            }

        return None

    @staticmethod
    def preprocess_plate(plate_image: np.ndarray) -> np.ndarray:
        """Preprocess license plate image for OCR."""
        # Convert to grayscale if needed
        if len(plate_image.shape) == 3:
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_image

        # Resize to standard size
        height, width = gray.shape
        if width > height:
            gray = cv2.resize(gray, (300, int(300 * height / width)))
        else:
            gray = cv2.resize(gray, (int(300 * width / height), 300))

        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh