"""
Utility functions for CasePoint
"""

import re


def extract_journal_from_citation(citation_text):
    """
    Extract journal abbreviation from citation text.
    
    Supports: PLD, MLD, SCMR, YLR, CLC, CLD, PCrLJ, PTD, PLC
    
    Args:
        citation_text: Citation string (e.g., "2003 MLD 1077")
        
    Returns:
        str: Journal abbreviation in uppercase (e.g., "MLD") or None if not found
    """
    if not citation_text:
        return None
        
    match = re.search(r'\b(PLD|MLD|SCMR|YLR|CLC|CLD|PCrLJ|PTD|PLC)\b', citation_text, re.IGNORECASE)
    return match.group(1).upper() if match else None
