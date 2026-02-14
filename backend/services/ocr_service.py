"""
Tesseract OCR service for text extraction from images.

PRIVACY NOTICE:
OCR processing is performed entirely locally using Tesseract.
Extracted text is held in memory only during request processing.
No text is permanently stored or transmitted externally.
"""

import pytesseract
import numpy as np
import platform
import os
from PIL import Image
from io import BytesIO

from services.preprocessing import preprocess_image


def _configure_tesseract():
    """Configure Tesseract binary path for Windows."""
    if platform.system() == "Windows":
        # Common Windows installation paths
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(
                os.environ.get("USERNAME", "")
            ),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return
        # If not found, rely on PATH
        print("WARNING: Tesseract not found at common paths. Ensure it is in PATH.")


# Configure on module load
_configure_tesseract()


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from an image using Tesseract OCR.
    
    Pipeline:
    1. Preprocess image with OpenCV (deskew, denoise, threshold)
    2. Run Tesseract OCR on preprocessed image
    3. Return extracted text (in-memory only)
    
    Args:
        image_bytes: Raw image bytes.
        
    Returns:
        Extracted text string.
    """
    # Preprocess image for better OCR accuracy
    preprocessed = preprocess_image(image_bytes)

    # Convert numpy array to PIL Image for pytesseract
    pil_image = Image.fromarray(preprocessed)

    # Run Tesseract with optimized config for invoices
    custom_config = r"--oem 3 --psm 6"
    text = pytesseract.image_to_string(pil_image, config=custom_config)

    return text.strip()


def extract_text_from_image_raw(image_bytes: bytes) -> str:
    """
    Extract text from an image WITHOUT preprocessing.
    Used as a fallback if preprocessing produces worse results.
    """
    pil_image = Image.open(BytesIO(image_bytes))
    custom_config = r"--oem 3 --psm 6"
    text = pytesseract.image_to_string(pil_image, config=custom_config)
    return text.strip()
