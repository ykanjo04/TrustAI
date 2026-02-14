"""
Image preprocessing pipeline for OCR optimization.

Uses OpenCV for:
- Grayscale conversion
- Noise removal (Gaussian blur)
- Contrast normalization (CLAHE)
- Adaptive thresholding
- Deskewing

PRIVACY NOTICE:
All image processing is done in-memory using numpy arrays.
No images are saved to disk at any point.
"""

import cv2
import numpy as np
from typing import Optional


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Full preprocessing pipeline for an invoice/receipt image.
    
    Args:
        image_bytes: Raw image bytes from upload.
        
    Returns:
        Preprocessed image as numpy array, optimized for OCR.
    """
    # Decode image from bytes (in-memory, no disk I/O)
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image from provided bytes.")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Noise removal with Gaussian blur
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)

    # Contrast normalization using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Deskew the image
    deskewed = _deskew(enhanced)

    # Adaptive thresholding for better text extraction
    thresh = cv2.adaptiveThreshold(
        deskewed, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    return thresh


def _deskew(image: np.ndarray) -> np.ndarray:
    """
    Correct image skew using minimum area rectangle on contours.
    """
    coords = np.column_stack(np.where(image > 0))
    if len(coords) < 10:
        return image

    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Only deskew if the angle is significant but not too extreme
    if abs(angle) > 0.5 and abs(angle) < 15:
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return rotated

    return image


def image_to_base64_preview(image_bytes: bytes) -> Optional[str]:
    """
    Convert image bytes to a base64 string for frontend preview.
    Does not store anything to disk.
    """
    import base64
    try:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return encoded
    except Exception:
        return None
