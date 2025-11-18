"""
Legal Metadata Extraction Utilities
Extract court, parties, journal, and year from Pakistan legal citations.
"""

import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def extract_court_from_citation(citation: str, full_text: Optional[str] = None) -> str:
    """
    Extract and normalize court name from citation.
    
    Normalization rules:
    - "Lahore" -> "Lahore High Court"
    - "Karachi" -> "Sindh High Court"
    - "Peshawar" -> "Peshawar High Court"
    - "Quetta" or "Balochistan" -> "Balochistan High Court"
    - "Islamabad" -> "Islamabad High Court"
    - "Supreme Court" or "SC" -> "Supreme Court of Pakistan"
    - "Federal Shariat Court" or "FSC" -> "Federal Shariat Court"
    
    Args:
        citation: Citation string (e.g., "PLD 1984 SC 191")
        full_text: Optional full text for additional context
        
    Returns:
        Normalized court name
    """
    citation_upper = citation.upper()
    
    # Check for Supreme Court
    if re.search(r'\bSUPREME\s+COURT\b', citation_upper) or re.search(r'\bSC\b', citation_upper):
        return "Supreme Court of Pakistan"
    
    # Check for Federal Shariat Court
    if re.search(r'\bFEDERAL\s+SHARIAT\s+COURT\b', citation_upper) or re.search(r'\bFSC\b', citation_upper):
        return "Federal Shariat Court"
    
    # Check for High Courts
    if re.search(r'\bLAHORE\b', citation_upper):
        return "Lahore High Court"
    
    if re.search(r'\bKARACHI\b', citation_upper):
        return "Sindh High Court"
    
    if re.search(r'\bPESHAWAR\b', citation_upper):
        return "Peshawar High Court"
    
    if re.search(r'\bQUETTA\b', citation_upper) or re.search(r'\bBALOCHISTAN\b', citation_upper):
        return "Balochistan High Court"
    
    if re.search(r'\bISLAMABAD\b', citation_upper):
        return "Islamabad High Court"
    
    if re.search(r'\bAJK\b', citation_upper):
        return "Azad Jammu & Kashmir High Court"
    
    # Default fallback
    return "Unknown Court"


def extract_parties(full_text: str, journal: str) -> str:
    """
    Extract party names from citation text.
    
    Rules:
    - PLD: Join lines 3, 4, 5
    - MLD/CLC/CLD: Join lines 4, 5, 6
    - Others: Use first non-empty lines after citation
    
    Args:
        full_text: Full text of the citation
        journal: Journal code (e.g., "PLD", "MLD")
        
    Returns:
        Party names as single clean line (e.g., "Muhammad Imran v. The State")
    """
    if not full_text:
        return ""
    
    # Split into lines and remove empty ones
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    
    if len(lines) < 6:
        # Not enough lines, return what we have
        return " ".join(lines[:3])
    
    # Apply journal-specific rules
    if journal == 'PLD':
        # Lines 3, 4, 5 (zero-indexed: 2, 3, 4)
        party_lines = lines[2:5]
    elif journal in ['MLD', 'CLC', 'CLD']:
        # Lines 4, 5, 6 (zero-indexed: 3, 4, 5)
        party_lines = lines[3:6]
    else:
        # Default: first 3 lines after citation
        party_lines = lines[2:5]
    
    # Join and clean
    parties = " ".join(party_lines)
    parties = re.sub(r'\s+', ' ', parties)  # Normalize whitespace
    
    # Remove common prefixes
    parties = re.sub(r'^(Case|Appeal|Petition|Application|Review)\s*:\s*', '', parties, flags=re.IGNORECASE)
    
    return parties.strip()


def extract_journal_year(citation: str) -> Tuple[str, int]:
    """
    Extract journal code and year from citation.
    
    Examples:
        "PLD 1984 SC 191" -> ("PLD", 1984)
        "2020 MLD 456" -> ("MLD", 2020)
        
    Args:
        citation: Citation string
        
    Returns:
        Tuple of (journal_code, year)
    """
    citation = citation.strip()
    
    # Extract year (4-digit number starting with 19 or 20)
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', citation)
    year = int(year_match.group(1)) if year_match else 0
    
    # Extract journal code
    journal_codes = ['PLD', 'MLD', 'YLR', 'CLD', 'CLC', 'SCMR', 'PCrLJ', 'PTD', 'PLC']
    journal = "Unknown"
    
    for code in journal_codes:
        if re.search(rf'\b{code}\b', citation, re.IGNORECASE):
            journal = code
            break
    
    return journal, year


def normalize_citation(citation: str) -> str:
    """
    Normalize citation format for consistency.
    
    Examples:
        "pld 1984 sc 191" -> "PLD 1984 SC 191"
        "  2020  MLD  456  " -> "2020 MLD 456"
    """
    # Uppercase
    citation = citation.upper()
    
    # Normalize whitespace
    citation = re.sub(r'\s+', ' ', citation)
    
    return citation.strip()
