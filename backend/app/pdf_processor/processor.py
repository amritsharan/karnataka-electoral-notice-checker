import os
import io
import logging
from typing import List, Dict, Any, Tuple

# pyrefly: ignore [missing-import]
import fitz  # type: ignore # PyMuPDF

# pyrefly: ignore [missing-import]
try:
    import pytesseract  # type: ignore
    # pyrefly: ignore [missing-import]
    from PIL import Image  # type: ignore
    HAS_OCR = True
except Exception:
    HAS_OCR = False

from .epic_extractor import extract_epics_with_context

logger = logging.getLogger(__name__)

# Minimum characters extracted per page before triggering OCR fallback
TEXT_THRESHOLD = 50

def process_pdf_bytes(pdf_bytes: bytes, document_name: str = "document.pdf") -> Tuple[List[Dict[str, Any]], int, bool]:
    """
    Processes PDF bytes:
    1. Opens PDF using PyMuPDF (fitz)
    2. Extracts text page by page
    3. If text per page < TEXT_THRESHOLD, attempts OCR if available
    4. Extracts EPICs and context from each page
    
    Returns:
    (records, total_pages, ocr_used)
    """
    records = []
    ocr_used = False
    total_pages = 0

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]
            page_text = page.get_text("text")

            # Check if page is scanned / text threshold not met
            if len(page_text.strip()) < TEXT_THRESHOLD:
                # Attempt OCR fallback
                ocr_text = try_ocr_page(page)
                if ocr_text:
                    page_text = ocr_text
                    ocr_used = True

            # Extract EPIC records from page text
            page_records = extract_epics_with_context(page_text, page_num=page_num)
            records.extend(page_records)

        doc.close()
    except Exception as e:
        logger.error(f"Error processing PDF {document_name}: {e}")
        raise e

    return records, total_pages, ocr_used


def process_pdf_content(
    pdf_bytes: bytes,
    pdf_path: str = "document.pdf",
    enable_ocr: bool = True
) -> Tuple[str, bool]:
    """
    Extract text content from PDF for EPIC processing.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        pdf_path: Document name for logging
        enable_ocr: Whether to attempt OCR if text extraction fails
        
    Returns:
        (extracted_text, ocr_used)
    """
    ocr_used = False
    extracted_text = ""
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text("text")
            
            # Check if page is scanned / text threshold not met
            if enable_ocr and len(page_text.strip()) < TEXT_THRESHOLD:
                # Attempt OCR fallback
                ocr_text = try_ocr_page(page)
                if ocr_text:
                    page_text = ocr_text
                    ocr_used = True
            
            text_parts.append(page_text)
        
        extracted_text = "\n".join(text_parts)
        doc.close()
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        raise e
    
    return extracted_text, ocr_used


def try_ocr_page(page) -> str:
    """
    Renders PyMuPDF page as pixmap image and runs Tesseract OCR if installed.
    """
    if not HAS_OCR:
        return ""
    try:
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_text = pytesseract.image_to_string(img)
        return ocr_text
    except Exception as e:
        logger.debug(f"OCR not available or failed: {e}")
        return ""


