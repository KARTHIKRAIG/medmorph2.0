 
import cv2
import pytesseract
import numpy as np
from PIL import Image
import re
import os

class PrescriptionOCR:
    def __init__(self):
        # Configure Tesseract path for Windows
        if os.name == 'nt':  # Windows
            pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

        # Configure multiple Tesseract configurations for different scenarios
        self.configs = [
            r'--oem 3 --psm 6',  # Default configuration
            r'--oem 3 --psm 3',  # Fully automatic page segmentation
            r'--oem 3 --psm 4',  # Assume a single column of text
            r'--oem 3 --psm 8',  # Treat the image as a single word
            r'--oem 3 --psm 13'  # Raw line. Treat the image as a single text line
        ]
    
    def preprocess_image(self, image_path):
        """Preprocess the image for better OCR results with multiple methods"""
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image at {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Try multiple preprocessing approaches
        processed_images = []

        # Method 1: Basic preprocessing
        denoised = cv2.fastNlMeansDenoising(gray)
        _, binary1 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('basic', binary1))

        # Method 2: Adaptive thresholding
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY, 31, 2)
        processed_images.append(('adaptive', adaptive))

        # Method 3: Morphological operations
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        _, binary2 = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('morph', binary2))

        return processed_images

    def extract_text(self, image_path):
        """Extract text from a prescription image using multiple configs and preprocessing"""
        processed_images = self.preprocess_image(image_path)
        results = []
        for method, img in processed_images:
            for config in self.configs:
                text = pytesseract.image_to_string(img, config=config)
                results.append((method, config, text.strip()))
        # Return the best result (longest text)
        best = max(results, key=lambda x: len(x[2]))
        return best[2] if best[2] else "No text extracted"
