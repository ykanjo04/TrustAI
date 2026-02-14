"""
PDF text extraction service.

Uses PyMuPDF (fitz) to:
1. Check if PDF has embedded text (digital PDF) -> extract directly
2. If scanned PDF -> convert pages to images -> route to OCR pipeline

PRIVACY NOTICE:
PDF processing is done entirely in-memory.
No PDF files or extracted content are saved to disk.
"""

import fitz  # PyMuPDF
from typing import Tuple


def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, bool]:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_bytes: Raw PDF file bytes.
        
    Returns:
        Tuple of (extracted_text, is_digital).
        is_digital indicates whether text was extracted directly (True)
        or via OCR fallback (False).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    full_text = ""
    for page in doc:
        page_text = page.get_text()
        if page_text.strip():
            full_text += page_text + "\n"
    
    doc.close()
    
    # If we got meaningful text, it's a digital PDF
    if len(full_text.strip()) > 20:
        return full_text.strip(), True
    
    # Otherwise, it's a scanned PDF - convert to images for OCR
    return _pdf_to_ocr(pdf_bytes)


def _pdf_to_ocr(pdf_bytes: bytes) -> Tuple[str, bool]:
    """
    Convert scanned PDF pages to images and run OCR.
    All processing in-memory.
    """
    from services.ocr_service import extract_text_from_image
    
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    
    for page in doc:
        # Render page to image at 300 DPI for good OCR quality
        pix = page.get_pixmap(dpi=300)
        image_bytes = pix.tobytes("png")
        
        page_text = extract_text_from_image(image_bytes)
        if page_text:
            full_text += page_text + "\n"
    
    doc.close()
    
    return full_text.strip(), False


def get_pdf_page_as_image(pdf_bytes: bytes, page_num: int = 0) -> bytes:
    """
    Get a specific PDF page as PNG image bytes for preview.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    if page_num >= len(doc):
        page_num = 0
    
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    image_bytes = pix.tobytes("png")
    
    doc.close()
    return image_bytes
