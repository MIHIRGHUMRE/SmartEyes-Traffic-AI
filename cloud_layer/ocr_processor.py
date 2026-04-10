import easyocr
import re
import numpy as np

class OCRProcessor:
    def __init__(self):
        # Initialize EasyOCR for English
        self.reader = easyocr.Reader(['en'], gpu=False) # Forced to CPU to avoid CUDA mismatch exceptions
        
    def extract_number_plate(self, image_array):
        """
        Extract text from an image array.
        :param image_array: Numpy array of the image (BGR from OpenCV).
        :return: string (the best guessed number plate text)
        """
        # Run EasyOCR
        results = self.reader.readtext(image_array)
        
        candidates = []
        for (bbox, text, prob) in results:
            # Basic cleaning to keep only alphanumeric
            clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
            # A typical Indian number plate has around 9 to 10 characters (e.g. MH12AB1234)
            if len(clean_text) >= 5:
                candidates.append((clean_text, prob))
                
        if candidates:
            # Return the highest probability candidate
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
            
        return "UNKNOWN_PLATE"
