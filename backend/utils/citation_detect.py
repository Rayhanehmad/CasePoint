"""
Legal Citation Detection for Pakistan Journals
Detects PLD, MLD, YLR, CLD, CLC, SCMR, PCrLJ, PTD, PLC citations with page mapping.
"""

import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

# Regex patterns for each journal (case-insensitive)
JOURNAL_PATTERNS = {
    'PLD': r'\bPLD\s+\d{4}\s+(?:Supreme Court|SC|Federal Shariat Court|FSC|Lahore|Karachi|Peshawar|Quetta|Islamabad|AJK)\s+\d+\b',
    'MLD': r'\b\d{4}\s+MLD\s+\d+\b',
    'YLR': r'\b\d{4}\s+YLR\s+\d+\b',
    'CLD': r'\b\d{4}\s+CLD\s+\d+\b',
    'CLC': r'\b\d{4}\s+CLC\s+\d+\b',
    'SCMR': r'\b\d{4}\s+SCMR\s+\d+\b',
    'PCrLJ': r'\b\d{4}\s+PCrLJ\s+\d+\b',
    'PTD': r'\b\d{4}\s+PTD\s+\d+\b',
    'PLC': r'\b\d{4}\s+PLC\s+\d+\b',
}


def detect_headings(full_text: str, page_texts: List[str]) -> List[Dict]:
    """
    Detect all legal citation headings with their page locations.
    
    Args:
        full_text: Combined text from entire document
        page_texts: List of text per page (for page mapping)
        
    Returns:
        List of dicts with keys:
        - citation: Full citation string (e.g., "PLD 1984 SC 191")
        - journal: Journal code (e.g., "PLD")
        - year: Year (int)
        - match_start_idx: Character index in full_text
        - page_index: Zero-based page number
        - page_range_start: Start page for this citation
        - page_range_end: End page for this citation (exclusive)
    """
    headings = []
    
    # Build cumulative character positions for each page
    page_char_positions = [0]  # Start of page 0
    for page_text in page_texts:
        # Add 2 for the "\n\n" separator between pages
        page_char_positions.append(page_char_positions[-1] + len(page_text) + 2)
    
    # Detect all citations across all journals
    for journal, pattern in JOURNAL_PATTERNS.items():
        matches = re.finditer(pattern, full_text, re.IGNORECASE)
        
        for match in matches:
            citation = match.group(0)
            match_start = match.start()
            
            # Determine which page this citation is on
            page_idx = _find_page_for_char_index(match_start, page_char_positions)
            
            # Extract year from citation
            year = _extract_year_from_citation(citation)
            
            headings.append({
                'citation': citation,
                'journal': journal,
                'year': year,
                'match_start_idx': match_start,
                'page_index': page_idx
            })
    
    # Sort by page index and character position
    headings.sort(key=lambda h: (h['page_index'], h['match_start_idx']))
    
    # Assign page ranges (current heading page to next heading page - 1)
    for i, heading in enumerate(headings):
        heading['page_range_start'] = heading['page_index']
        
        if i < len(headings) - 1:
            # Range goes up to (but not including) next heading's page
            heading['page_range_end'] = headings[i + 1]['page_index']
        else:
            # Last heading goes to end of document
            heading['page_range_end'] = len(page_texts)
    
    logger.info(f"Detected {len(headings)} citations across {len(page_texts)} pages")
    
    return headings


def _find_page_for_char_index(char_idx: int, page_char_positions: List[int]) -> int:
    """
    Find which page contains the given character index.
    
    Args:
        char_idx: Character position in full_text
        page_char_positions: List of cumulative character positions
        
    Returns:
        Zero-based page index
    """
    for i in range(len(page_char_positions) - 1):
        if page_char_positions[i] <= char_idx < page_char_positions[i + 1]:
            return i
    
    # If beyond all pages, assign to last page
    return len(page_char_positions) - 2


def _extract_year_from_citation(citation: str) -> int:
    """Extract year from citation string"""
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', citation)
    if year_match:
        return int(year_match.group(1))
    return 0


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
