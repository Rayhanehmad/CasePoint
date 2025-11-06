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


def extract_court_from_citation(citation_text, full_text=None):
    """
    Extract the court name from various Pakistan law citation formats:
    Handles PLD, MLD, SCMR, YLR, CLC, CLD, PCrLJ, PTD, PLC.
    Converts jurisdiction names to full court names (e.g., "Lahore" → "Lahore High Court").
    
    Args:
        citation_text: Citation string (e.g., "PLD 2025 Federal Shariat Court 1")
        full_text: Optional full text for multiline MLD format
        
    Returns:
        str: Court name (e.g., "Federal Shariat Court", "Lahore High Court") or None if not found
    """
    if not citation_text:
        return None

    text = citation_text.strip()
    
    # Jurisdiction to Court mapping for High Courts
    jurisdiction_map = {
        'Lahore': 'Lahore High Court',
        'Karachi': 'Sindh High Court',
        'Sindh': 'Sindh High Court',
        'Peshawar': 'Peshawar High Court',
        'Quetta': 'Balochistan High Court',
        'Balochistan': 'Balochistan High Court',
        'Islamabad': 'Islamabad High Court',
        'AJK': 'Azad Jammu and Kashmir High Court',
        'Azad Kashmir': 'Azad Jammu and Kashmir High Court',
    }

    # --- 1️⃣ PLD FORMAT ---
    # e.g., PLD 2025 Federal Shariat Court 1 → Federal Shariat Court
    match_pld = re.search(r"PLD\s+\d{4}\s+([A-Za-z\s]+?)\s+\d+", text)
    if match_pld:
        court = match_pld.group(1).strip()
        # Check if it's a jurisdiction name that needs "High Court" appended
        return jurisdiction_map.get(court, court)

    # --- 2️⃣ MLD FORMAT (inline) ---
    # e.g., 2003 MLD 1075 [Lahore] → Lahore High Court
    match_mld = re.search(r"\[\s*([A-Za-z\s]+?)\s*\]", text)
    if match_mld:
        jurisdiction = match_mld.group(1).strip()
        return jurisdiction_map.get(jurisdiction, jurisdiction + ' High Court')

    # --- 3️⃣ SCMR FORMAT ---
    # e.g., 2023 SCMR 511 Supreme Court → Supreme Court
    match_scmr = re.search(r"SCMR\s+\d+\s+([A-Za-z\s]+)", text)
    if match_scmr:
        court = match_scmr.group(1).strip()
        return jurisdiction_map.get(court, court)

    # --- 4️⃣ Other Journals (YLR, CLD, etc.) ---
    match_other = re.search(
        r"\b(?:YLR|CLC|CLD|PCrLJ|PTD|PLC)\s+(?:\d{4}\s+)?([A-Za-z\s]+?)\s+\d+", text
    )
    if match_other:
        court = match_other.group(1).strip()
        return jurisdiction_map.get(court, court)

    # --- 5️⃣ Multiline MLD (court in 2nd line) ---
    if full_text:
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]
        if len(lines) >= 2:
            second_line = lines[1]
            mld_bracket = re.search(r"\[\s*([A-Za-z\s]+)\s*\]", second_line)
            if mld_bracket:
                jurisdiction = mld_bracket.group(1).strip()
                return jurisdiction_map.get(jurisdiction, jurisdiction + ' High Court')

    return None
