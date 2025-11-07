
# utils_extract_parties.py — Contains party extraction + preview + highlight functions

import re

def highlight_keywords(text, keywords):
    """Highlight keywords in red + bold."""
    if not text:
        return ""

    for kw in keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        text = pattern.sub(
            lambda m: f'<span class="keyword-highlight">{m.group(0)}</span>',
            text
        )
    return text


def extract_preview_paragraph(full_text):
    """Skip top 6 lines and return next preview paragraph."""
    if not full_text:
        return ""

    lines = [line.strip() for line in full_text.split("\n") if line.strip()]

    if len(lines) <= 6:
        return " ".join(lines)

    trimmed = lines[6:]  # skip first 6 lines
    paragraph = " ".join(trimmed[:5])  # next 3–5 lines
    return paragraph


def extract_parties(full_text, journal):
    """Extract petitioner/respondent lines based on journal rules."""

    if not full_text:
        return ""

    lines = [line.strip() for line in full_text.split("\n") if line.strip()]

    if len(lines) < 7:
        return ""

    journal = journal.upper()

    if journal == "PLD":
        selected = lines[2:5]        # line 3,4,5
    elif journal in ["MLD", "CLC", "CLD"]:
        selected = lines[3:6]        # line 4,5,6
    else:
        selected = []

    return " ".join(selected).replace("  ", " ").strip()
