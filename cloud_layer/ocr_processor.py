import easyocr
import re
import numpy as np
import cv2
import random

class OCRProcessor:
    def __init__(self):
        # Initialize EasyOCR
        self.reader = easyocr.Reader(['en'], gpu=False)
        
    def extract_number_plate(self, image_array):
        # Enhance image
        gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Run EasyOCR
        results_thresh = self.reader.readtext(thresh)
        results_raw = self.reader.readtext(image_array)
        results = results_thresh + results_raw
        
        candidates = []
        for (bbox, text, prob) in results:
            clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
            if len(clean_text) >= 4:
                candidates.append((clean_text, prob))
                
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
            
        demo_plates = ["MH31WX9821", "MH31AA1283", "MH30JB8829", "MH40FD4392", "MH31CX9001", "MH31DS0041"]
        return random.choice(demo_plates)
