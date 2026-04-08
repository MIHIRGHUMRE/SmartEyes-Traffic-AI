try:
    import os
    os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False
    PaddleOCR = None
    print("Warning: PaddleOCR not available. OCR functionality will be limited.")

import cv2
import numpy as np
from typing import List, Dict, Optional
import re

class LicensePlateOCR:
    """OCR for license plate text recognition using PaddleOCR or fallback."""

    def __init__(self, lang: str = 'en', use_gpu: bool = False):
        """
        Initialize PaddleOCR or fallback.

        Args:
            lang: Language for OCR
            use_gpu: Whether to use GPU
        """
        if PADDLE_AVAILABLE:
            self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=use_gpu, show_log=False)
            self.method = 'paddle'
        else:
            self.ocr = None
            self.method = 'fallback'
            print("Using fallback OCR method (limited functionality)")

    def extract_text(self, plate_images: List[np.ndarray]) -> List[Dict]:
        """
        Extract text from license plate images.

        Args:
            plate_images: List of license plate images

        Returns:
            List of OCR results with text and confidence
        """
        if self.method == 'paddle' and PADDLE_AVAILABLE:
            return self._extract_with_paddle(plate_images)
        else:
            return self._extract_with_fallback(plate_images)

    def _extract_with_paddle(self, plate_images: List[np.ndarray]) -> List[Dict]:
        """Extract text using PaddleOCR."""
        results = []

        for img in plate_images:
            # Preprocess image
            processed = self._preprocess_image(img)

            # Run OCR
            ocr_result = self.ocr.ocr(processed, cls=True)

            if ocr_result and ocr_result[0]:
                # Extract text and confidence
                text_results = []
                for line in ocr_result[0]:
                    text = line[1][0]
                    confidence = line[1][1]
                    text_results.append({
                        'text': text,
                        'confidence': confidence
                    })

                # Combine text if multiple lines
                combined_text = ' '.join([r['text'] for r in text_results])
                avg_confidence = np.mean([r['confidence'] for r in text_results])

                # Clean and validate license plate format
                cleaned_text = self._clean_license_plate(combined_text)

                results.append({
                    'text': cleaned_text,
                    'confidence': avg_confidence,
                    'raw_results': text_results
                })
            else:
                results.append({
                    'text': '',
                    'confidence': 0.0,
                    'raw_results': []
                })

        return results

    def _extract_with_fallback(self, plate_images: List[np.ndarray]) -> List[Dict]:
        """Fallback OCR method using basic image processing."""
        results = []

        for img in plate_images:
            # Simple fallback - just return placeholder
            # In a real implementation, you could use Tesseract or other OCR
            results.append({
                'text': 'DETECTED',  # Placeholder text
                'confidence': 0.5,   # Low confidence
                'raw_results': [{'text': 'DETECTED', 'confidence': 0.5}],
                'note': 'Using fallback OCR - install PaddleOCR for better results'
            })

        return results

    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        # Convert to grayscale if needed
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Resize if too small
        height, width = gray.shape
        if width < 100 or height < 30:
            scale = max(100 / width, 30 / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            gray = cv2.resize(gray, (new_width, new_height))

        # Enhance contrast
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

        # Apply Gaussian blur to reduce noise
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh

    def _clean_license_plate(self, text: str) -> str:
        """Clean and format license plate text."""
        # Remove spaces and special characters
        cleaned = re.sub(r'[^A-Za-z0-9]', '', text.upper())

        # Common license plate formats (Indian format example)
        # XX00XX0000 or XX00XX00X
        if re.match(r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$', cleaned):
            return cleaned
        elif re.match(r'^[A-Z]{2}\d{2}[A-Z]{2}\d{2}[A-Z]$', cleaned):
            return cleaned
        else:
            # Return cleaned text even if format doesn't match
            return cleaned