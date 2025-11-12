"""
Bulk Citation Extractor - backend/services/bulk_processor.py

This module processes continuous legal documents (TXT/DOCX/PDF->text) and:
- Normalizes spaced-letter reporters (e.g., "P L D" -> "PLD", "S C M R" -> "SCMR", "C L D" -> "CLD").
- Splits a continuous document (no headings/new pages) into individual citation blocks using reporter starts as anchors.
- Treats occurrences of reporters (spaced or not) as the start of a new citation.
- For each citation block:
  - Extracts the top six (6) textual lines after the start anchor and marks them as the "headline".
  - Prepares the headline as centered and bold HTML for the "View Full Text" UI.
  - Ensures there is a blank line after the top-six headline lines in the stored "full_text" representation.

The file exposes:
- process_document_text(text: str) -> List[Dict[str,str]]
- read_docx_text(path: str) -> str (optional, requires python-docx)
- _selftest() quick unit-style checks

Note: This file was edited to fix an AttributeError when building the combined ANCHOR_PATTERN. The previous code attempted to call .group(0) on compiled regex objects. That has been corrected by using the .pattern attribute of each compiled regex.
"""

import re
from typing import List, Dict

try:
    # optional: used only if you want to read .docx files directly in this module
    from docx import Document
except Exception:
    Document = None  # python-docx not installed; caller can supply plain text


# -----------------------------
# Config: reporters and patterns
# -----------------------------
CANONICAL_REPORTERS = ["PLD", "SCMR", "CLD"]

# Generic spaced-letter sequence matcher (used for normalization only)
SPACED_LETTER_RE = re.compile(r"\b(?:(?:[A-Za-z]\s+){1,5}[A-Za-z])\b")

# Build reporter matcher patterns (without surrounding \b) that recognize either normal or spaced forms.
REPORTER_MATCHERS: List[re.Pattern] = []
for rpt in CANONICAL_REPORTERS:
    spaced = " ".join(list(rpt))
    # pattern matches either exact reporter (PLD) or spaced form (P L D)
    pat = rf"(?:{re.escape(rpt)}|{re.escape(spaced)})"
    REPORTER_MATCHERS.append(re.compile(pat, re.IGNORECASE))

# Combined anchor matcher (we wrap with word boundaries here once)
combined_inner = "|".join(p.pattern for p in REPORTER_MATCHERS)
ANCHOR_PATTERN = re.compile(rf"\b(?:{combined_inner})\b", re.IGNORECASE)


# -----------------------------
# Helpers
# -----------------------------

def normalize_spaced_reporters(text: str) -> str:
    """Replace spaced-letter reporters like 'P L D' with 'PLD'. Also normalizes spaced forms for SCMR, CLD.

    Collapses sequences like "P  L   D" -> "PLD" and trims extra spaces. Returns the transformed text.
    """

    def collapse_match(m: re.Match) -> str:
        token = m.group(0)
        letters = re.sub(r"\s+", "", token).upper()
        if letters in CANONICAL_REPORTERS:
            return letters
        return letters

    # First target known spaced reporters explicitly (to avoid accidental transformations)
    for rpt in CANONICAL_REPORTERS:
        spaced = " ".join(list(rpt))
        text = re.sub(rf"\b{re.escape(spaced)}\b", rpt, text, flags=re.IGNORECASE)

    # Collapse generic spaced-letter sequences (best-effort)
    text = re.sub(r"\b([A-Za-z](?:\s+[A-Za-z]){1,5})\b", lambda m: collapse_match(m), text)

    return text


def find_anchor_positions(text: str) -> List[re.Match]:
    """Find anchor matches (reporter occurrences) and return list of Match objects sorted by start index."""
    matches: List[re.Match] = []
    for pattern in REPORTER_MATCHERS:
        for m in pattern.finditer(text):
            matches.append(m)
    matches.sort(key=lambda mm: mm.start())
    return matches


def split_into_citation_blocks(text: str) -> List[str]:
    """Split normalized text into blocks using reporter anchors as start points.

    Each block runs from one anchor start to the next anchor start (exclusive). If no anchors found, returns the whole text as one block.
    """
    if not text:
        return []

    normalized = normalize_spaced_reporters(text)
    anchors = find_anchor_positions(normalized)
    if not anchors:
        return [normalized.strip()]

    blocks: List[str] = []
    for i, m in enumerate(anchors):
        start = m.start()
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(normalized)
        block = normalized[start:end].strip()
        if block:
            blocks.append(block)
    return blocks


def extract_headline_and_format(block_text: str, headline_lines: int = 6) -> Dict[str, str]:
    """From a block of text, extract top N lines as headline and return HTML-formatted headline and full_text_with_spacing.

    The function returns dict with keys: headline_html, full_text_with_spacing, raw_text
    """
    # Split on CRLF or LF
    lines = re.split(r"\r?\n", block_text)

    # If there are no explicit line breaks, create pseudo-lines by splitting sentences
    if len(lines) == 1:
        sentences = re.split(r'(?<=[\.\?\!])\s+(?=[A-Z])', block_text)
        lines = [s.strip() for s in sentences if s.strip()]

    headline = lines[:headline_lines]
    rest_lines = lines[headline_lines:]

    # Headline HTML (centered + bold); preserve line breaks with <br/>
    headline_lines_clean = [h.strip() for h in headline if h.strip()]
    headline_html = "<div style=\"text-align:center;font-weight:bold;\">" + "<br/>".join(headline_lines_clean) + "</div>"

    # Normalize paragraphs in the rest: collapse multiple blank lines and create single blank line between paragraphs
    def normalize_paragraphs(ls: List[str]) -> str:
        paras: List[str] = []
        buffer: List[str] = []
        for l in ls:
            if l.strip() == "":
                if buffer:
                    paras.append(" ".join(p.strip() for p in buffer))
                    buffer = []
            else:
                buffer.append(l)
        if buffer:
            paras.append(" ".join(p.strip() for p in buffer))
        return "\n\n".join(paras)

    rest_text = normalize_paragraphs(rest_lines)

    if rest_text:
        full_text_with_spacing = headline_html + "\n\n" + rest_text
    else:
        full_text_with_spacing = headline_html

    return {
        "headline_html": headline_html,
        "full_text_with_spacing": full_text_with_spacing,
        "raw_text": block_text,
    }


def process_document_text(text: str) -> List[Dict[str, str]]:
    """Top-level: accept raw text (from .docx or other source) and return a list of citation dicts.

    Each dict contains: normalized_reporter, normalized_citation_start, headline_html, full_text_with_spacing, raw_text
    """
    normalized_text = normalize_spaced_reporters(text)
    blocks = split_into_citation_blocks(normalized_text)
    results: List[Dict[str, str]] = []

    for block in blocks:
        m = ANCHOR_PATTERN.search(block)
        normalized_reporter = m.group(0).upper() if m else ""

        # Citation start: first 10 words (safe fallback)
        words = block.split()
        citation_start = " ".join(words[:10]) if words else ""

        formatted = extract_headline_and_format(block, headline_lines=6)

        results.append(
            {
                "normalized_reporter": normalized_reporter,
                "normalized_citation_start": citation_start,
                "headline_html": formatted["headline_html"],
                "full_text_with_spacing": formatted["full_text_with_spacing"],
                "raw_text": formatted["raw_text"],
            }
        )

    return results


# -----------------------------
# Optional helper to read .docx using python-docx
# -----------------------------

def read_docx_text(path: str) -> str:
    if Document is None:
        raise RuntimeError("python-docx is not installed. Install with 'pip install python-docx' to read .docx files.")
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)


# -----------------------------
# Self-test / Unit-style tests
# -----------------------------

def _selftest() -> None:
    sample_spaced = (
        "P L D 2020 Lahore 453 This is the summary of the first case. It continues without new heading or page. "
        "There may be multiple sentences. More text here. Next we have another citation. "
        "S C M R 1998 1234 Another case summary starts right away. It has some lines. More details."
    )

    sample_nonspaced = (
        "PLD 2020 Lahore 453 This is the same example but with normal reporter spacing. "
        "SCMR 1998 1234 Another case here."
    )

    # Test normalization
    normalized = normalize_spaced_reporters(sample_spaced)
    assert "PLD 2020 Lahore 453" in normalized and "SCMR 1998 1234" in normalized, "Normalization failed"

    # Test splitting into blocks
    blocks = split_into_citation_blocks(normalized)
    assert len(blocks) >= 2, f"Expected at least 2 blocks, got {len(blocks)}"

    # Test processing both spaced and non-spaced variants
    processed_spaced = process_document_text(sample_spaced)
    processed_nonspaced = process_document_text(sample_nonspaced)

    assert isinstance(processed_spaced, list) and len(processed_spaced) >= 2
    assert isinstance(processed_nonspaced, list) and len(processed_nonspaced) >= 2

    # Test no-anchor behavior
    no_anchor = "This doc has no known reporter. It's just plain text. Nothing to split."
    blocks_no_anchor = split_into_citation_blocks(no_anchor)
    assert len(blocks_no_anchor) == 1 and no_anchor.strip() in blocks_no_anchor[0]

    # Check headline formatting and blank-line insertion
    for item in processed_spaced:
        assert "headline_html" in item and item["headline_html"].startswith("<div"), "headline missing or not HTML"
        assert "full_text_with_spacing" in item

    print("All quick self-tests passed.")


# -----------------------------
# Compatibility wrapper for legacy API
# -----------------------------

import os
import logging

logger = logging.getLogger(__name__)

class BulkDocumentProcessor:
    """
    Compatibility wrapper that preserves the old API while using new citation processing.
    Orchestrates existing services (OCR, citation extraction) with new normalization logic.
    """
    
    def __init__(self):
        # Import services here to avoid circular imports
        from services import ocr_service
        from services.citation_extractor import citation_extractor
        from services.utils import extract_journal_from_citation, extract_court_from_citation
        
        self.ocr_service = ocr_service
        self.citation_extractor = citation_extractor
        self.extract_journal = extract_journal_from_citation
        self.extract_court = extract_court_from_citation
    
    def process_document(self, file_path: str, filename: str, user_id: int = None) -> Dict:
        """
        Legacy API: Process a document file and return structured result.
        Integrates new citation normalization with existing services.
        
        Returns:
            Dict with 'success', 'data' (LegalCitation fields), 'citation'
        """
        try:
            # 1. Extract text using trusted OCR service
            text = self.ocr_service.extract_text_from_file(file_path, filename)
            
            if not text or len(text.strip()) < 50:
                return {
                    'success': False,
                    'error': 'Could not extract sufficient text from document'
                }
            
            # 2. Normalize spaced reporters and process with NEW logic
            normalized_text = normalize_spaced_reporters(text)
            
            # 3. Extract metadata using existing citation_extractor
            metadata = self.citation_extractor.extract_metadata(normalized_text, filename)
            
            # 4. Apply NEW citation processing for headline formatting
            citation_blocks = process_document_text(text)
            headline_html = ''
            full_text_formatted = text
            
            if citation_blocks:
                first_block = citation_blocks[0]
                headline_html = first_block.get('headline_html', '')
                full_text_formatted = first_block.get('full_text_with_spacing', text)
            
            # 5. Build complete data structure for LegalCitation model
            citation_data = {
                'citation': metadata.get('citation', ''),
                'title': metadata.get('title', ''),
                'court': metadata.get('court', ''),
                'jurisdiction': metadata.get('jurisdiction', ''),
                'year': metadata.get('year'),
                'judges': metadata.get('judges', ''),
                'headnotes': metadata.get('headnotes', ''),
                'legal_area': metadata.get('legal_area', ''),
                'summary': metadata.get('summary', ''),
                'party_line': metadata.get('parties', ''),
                'full_text': full_text_formatted,
                'document_type': 'case',
                'journal': self.extract_journal(metadata.get('citation', '')),
                'uploaded_by': user_id
            }
            
            return {
                'success': True,
                'data': citation_data,
                'citation': metadata.get('citation', ''),
                'headline_html': headline_html,
                'all_citation_blocks': citation_blocks
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }


# Create a singleton instance for backward compatibility
bulk_processor = BulkDocumentProcessor()


if __name__ == "__main__":
    _selftest()
