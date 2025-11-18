"""
PDF Slicing Utility
Slices PDF files by page ranges and saves individual citation PDFs.
"""

import os
import logging
from typing import Optional
import pikepdf
import re

logger = logging.getLogger(__name__)


def slice_pdf_by_range(
    source_pdf_path: str,
    page_start: int,
    page_end: int,
    output_dir: str,
    citation: str,
    journal: str,
    year: int
) -> Optional[str]:
    """
    Slice PDF by page range and save to organized directory structure.
    
    Args:
        source_pdf_path: Path to the source PDF file
        page_start: Start page (zero-indexed)
        page_end: End page (exclusive, zero-indexed)
        output_dir: Base output directory (e.g., "/uploads/citations")
        citation: Full citation string (e.g., "PLD 1984 SC 191")
        journal: Journal code (e.g., "PLD")
        year: Year of citation
        
    Returns:
        Relative path to saved PDF (e.g., "citations/PLD/1984/PLD_1984_SC_191.pdf")
        or None if slicing fails
    """
    try:
        # Sanitize citation for filename
        safe_citation = _sanitize_filename(citation)
        
        # Build directory structure: <output_dir>/<journal>/<year>/
        journal_dir = os.path.join(output_dir, journal, str(year))
        os.makedirs(journal_dir, exist_ok=True)
        
        # Build filename
        filename = f"{safe_citation}.pdf"
        output_path = os.path.join(journal_dir, filename)
        
        # Slice PDF using pikepdf
        with pikepdf.open(source_pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            # Validate page range
            if page_start < 0 or page_end > total_pages:
                logger.warning(f"Invalid page range [{page_start}:{page_end}] for {total_pages} pages")
                page_start = max(0, page_start)
                page_end = min(total_pages, page_end)
            
            if page_start >= page_end:
                logger.error(f"Invalid range: start={page_start} >= end={page_end}")
                return None
            
            # Create new PDF with selected pages
            output_pdf = pikepdf.Pdf.new()
            
            for page_num in range(page_start, page_end):
                output_pdf.pages.append(pdf.pages[page_num])
            
            # Save sliced PDF
            output_pdf.save(output_path)
            
            # Return relative path from uploads directory
            relative_path = os.path.relpath(output_path, start=os.path.dirname(output_dir))
            
            logger.info(f"Sliced PDF saved: {relative_path} (pages {page_start+1}-{page_end})")
            
            return relative_path
            
    except Exception as e:
        logger.error(f"PDF slicing failed for {citation}: {str(e)}")
        return None


def _sanitize_filename(citation: str) -> str:
    """
    Sanitize citation string for use as filename.
    
    Examples:
        "PLD 1984 SC 191" -> "PLD_1984_SC_191"
        "2020 MLD 456" -> "2020_MLD_456"
    """
    # Replace spaces with underscores
    safe = citation.strip()
    
    # Remove or replace unsafe characters
    safe = re.sub(r'[^\w\s-]', '', safe)
    safe = re.sub(r'[\s]+', '_', safe)
    
    # Limit length (filesystem typically allows 255)
    max_length = 200
    if len(safe) > max_length:
        safe = safe[:max_length]
    
    return safe


def create_thumbnail(pdf_path: str, output_path: str) -> bool:
    """
    Create thumbnail from first page of PDF (optional feature).
    
    Args:
        pdf_path: Path to PDF file
        output_path: Path to save thumbnail (PNG)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from pdf2image import convert_from_path
        
        # Convert only first page
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
        
        if images:
            # Save as PNG
            images[0].save(output_path, 'PNG')
            logger.info(f"Thumbnail saved: {output_path}")
            return True
        
        return False
        
    except Exception as e:
        logger.warning(f"Thumbnail creation failed: {str(e)}")
        return False
