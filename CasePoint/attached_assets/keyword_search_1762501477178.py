
# CasePoint Keyword Search + Highlight + Preview (Full Backend Module)
# Save this file as keyword_search.py and import routes into your Flask app.

import re
from flask import request, jsonify
from sqlalchemy import or_
from app import app, db
from models import LegalCitation


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

    lines = [line.strip() for line in full_text.split("\n")]
    lines = [line for line in lines if line]   # remove empty lines

    if len(lines) <= 6:
        return " ".join(lines)

    trimmed = lines[6:]  # skip first 6 lines

    paragraph = " ".join(trimmed[:5])  # next 3–5 lines as preview
    return paragraph


@app.route("/api/search/keyword")
def search_keyword():
    """Full keyword search in citation, summary, and full_text."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})

    keywords = q.split()

    keyword_filter = or_(
        LegalCitation.full_text.ilike(f"%{q}%"),
        LegalCitation.full_text.ilike(f"%{keywords[0]}%"),
        LegalCitation.summary.ilike(f"%{keywords[0]}%"),
        LegalCitation.citation.ilike(f"%{keywords[0]}%"),
    )

    results = LegalCitation.query.filter(keyword_filter).limit(50).all()

    output = []
    for r in results:
        preview = extract_preview_paragraph(r.full_text)
        preview = highlight_keywords(preview, keywords)

        output.append({
            "citation": r.citation,
            "court": r.court,
            "journal": r.journal,
            "summary_preview": preview
        })

    return jsonify({
        "total": len(results),
        "results": output
    })
