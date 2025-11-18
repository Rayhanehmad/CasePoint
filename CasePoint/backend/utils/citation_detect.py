"""
Legal Citation Detection for Pakistan Journals
Detects PLD, MLD, YLR, CLD, CLC, SCMR, PCrLJ, PTD, PLC citations with page mapping.
"""

import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


def detect_headings(page_texts):
    """
    Detects citation headings that appear at the top of pages.
    Each new citation starts with a heading and a new page.
    Returns list of dicts [{citation, page_index, journal, year}, ...]
    """

    CITATION_PATTERN = re.compile(
        r"\b(?:PLD\s+\d{4}\s+(?:Supreme Court|SC|Federal Shariat Court|FSC|Lahore|Karachi|Peshawar|Quetta|Islamabad|AJK)|"
        r"\d{4}\s+(?:MLD|YLR|CLD|CLC|SCMR|PCrLJ|PTD|PLC))\s+\d+\b",
        flags=re.IGNORECASE
    )

    detected = []

    for page_index, text in enumerate(page_texts):
        if not text or len(text.strip()) < 20:
            continue

        # Search citation within first 15% of the page text
        cutoff = max(300, int(len(text) * 0.15))
        top_text = text[:cutoff]

        for match in CITATION_PATTERN.finditer(top_text):
            citation_text = match.group().strip()

            # Extract journal and year
            year = None
            journal = None
            parts = citation_text.split()
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    year = part
                elif part.isalpha() and len(part) >= 3:
                    journal = part.upper()

            detected.append({
                "citation": citation_text,
                "page_index": page_index,
                "journal": journal,
                "year": year
            })

    # Remove duplicates
    seen = set()
    clean = []
    for d in detected:
        if d["citation"] not in seen:
            clean.append(d)
            seen.add(d["citation"])

    # Add page ranges
    for i, heading in enumerate(clean):
        heading['page_range_start'] = heading['page_index']
        
        if i < len(clean) - 1:
            # Range goes up to (but not including) next heading's page
            heading['page_range_end'] = clean[i + 1]['page_index']
        else:
            # Last heading goes to end of document
            heading['page_range_end'] = len(page_texts)
    
    logger.info(f"Detected {len(clean)} citations across {len(page_texts)} pages")

    return clean


def validate_heading_quality(headings: List[Dict]) -> Tuple[bool, str]:
    """
    Validate detected headings for quality checks.
    
    Returns:
        Tuple of (is_valid, warning_message)
    """
    if not headings:
        return False, "No citations detected in document"
    
    # Check for suspiciously many citations (might be false positives)
    if len(headings) > 200:
        return False, f"Too many citations detected ({len(headings)}). Possible false positives."
    
    # Check for overlapping page ranges (shouldn't happen with proper detection)
    for i in range(len(headings) - 1):
        if headings[i]['page_range_end'] <= headings[i]['page_range_start']:
            return False, f"Invalid page range for citation: {headings[i]['citation']}"
    
    return True, ""
