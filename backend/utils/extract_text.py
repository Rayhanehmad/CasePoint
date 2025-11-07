"""
Universal PDF Text Extraction Utility
Extracts text from PDFs with automatic OCR fallback for scanned documents.
"""

import logging
import pdfplumber
from typing import Tuple, List, Optional
import re

logger = logging.getLogger(__name__)

# Soft fallback for OCR dependencies
OCR_AVAILABLE = False
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
    logger.info("OCR dependencies (pdf2image, pytesseract) are available")
except ImportError as e:
    logger.warning(f"OCR dependencies not available: {e}. Text-mode extraction only.")


def extract_text_from_pdf(file_path: str, use_ocr_fallback: bool = True) -> Tuple[str, List[str], bool]:
    """
    Extract text from PDF with automatic OCR fallback.
    
    Args:
        file_path: Path to the PDF file
        use_ocr_fallback: Whether to use OCR if text extraction yields sparse results
        
    Returns:
        Tuple of:
        - full_text: Combined text from all pages
        - page_texts: List of text per page
        - used_ocr: Whether OCR was used
        
    Raises:
        Exception: If extraction fails
    """
    try:
        # Step 1: Try pdfplumber text extraction first
        page_texts = []
        total_chars = 0
        
        with pdfplumber.open(file_path) as pdf:
            num_pages = len(pdf.pages)
            logger.info(f"Processing {num_pages} pages from {file_path}")
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                page_texts.append(text)
                total_chars += len(text.strip())
                
                if (i + 1) % 50 == 0:
                    logger.info(f"Processed {i + 1}/{num_pages} pages...")
        
        # Calculate text density (chars per page)
        avg_chars_per_page = total_chars / num_pages if num_pages > 0 else 0
        
        # If very sparse text (likely scanned PDF), try OCR
        is_sparse = avg_chars_per_page < 50  # Less than 50 chars/page suggests scan
        
        if is_sparse and use_ocr_fallback and OCR_AVAILABLE:
            logger.info(f"Low text density ({avg_chars_per_page:.1f} chars/page). Using OCR fallback...")
            page_texts = _extract_with_ocr(file_path, num_pages)
            full_text = "\n\n".join(page_texts)
            full_text = _normalize_text(full_text, page_texts)
            return full_text, page_texts, True
        
        elif is_sparse and use_ocr_fallback and not OCR_AVAILABLE:
            logger.warning("Sparse text detected but OCR not available. Returning text-mode results.")
        
        # Use text-mode results
        full_text = "\n\n".join(page_texts)
        full_text = _normalize_text(full_text, page_texts)
        
        return full_text, page_texts, False
        
    except Exception as e:
        logger.error(f"PDF text extraction failed for {file_path}: {str(e)}")
        raise


def _extract_with_ocr(file_path: str, num_pages: int) -> List[str]:
    """Extract text using OCR (pdf2image + pytesseract)"""
    page_texts = []
    
    try:
        # Convert PDF to images (page by page to save memory)
        images = convert_from_path(file_path, dpi=300)
        
        for i, image in enumerate(images):
            # Extract text via Tesseract
            text = pytesseract.image_to_string(image, lang='eng')
            page_texts.append(text.strip())
            
            # Free memory
            del image
            
            if (i + 1) % 10 == 0:
                logger.info(f"OCR processed {i + 1}/{num_pages} pages...")
        
        logger.info(f"OCR extraction complete for {num_pages} pages")
        return page_texts
        
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}")
        raise


def _normalize_text(full_text: str, page_texts: List[str]) -> str:
    """
    Normalize extracted text:
    - Remove excessive whitespace
    - Remove repeated headers/footers (simple heuristic)
    """
    # Normalize whitespace
    full_text = re.sub(r'\s+', ' ', full_text)
    full_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', full_text)
    
    # Simple heuristic: if same short line appears in 80%+ of pages, likely header/footer
    if len(page_texts) > 10:  # Only for multi-page docs
        line_frequency = {}
        
        for page in page_texts:
            lines = page.split('\n')
            for line in lines[:3] + lines[-3:]:  # Check first/last 3 lines
                line = line.strip()
                if len(line) < 100 and len(line) > 5:  # Short lines only
                    line_frequency[line] = line_frequency.get(line, 0) + 1
        
        # Remove lines that appear in >80% of pages
        threshold = len(page_texts) * 0.8
        repeated_lines = [line for line, count in line_frequency.items() if count > threshold]
        
        for line in repeated_lines:
            full_text = full_text.replace(line, '')
            logger.debug(f"Removed repeated header/footer: {line[:50]}...")
    
    return full_text.strip()
