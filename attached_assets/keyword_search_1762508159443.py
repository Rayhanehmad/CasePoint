
# keyword_search.py — Full Backend Keyword Search Module

from flask import request, jsonify
from sqlalchemy import or_
from app import app
from models import LegalCitation
from utils_extract_parties import (
    highlight_keywords,
    extract_preview_paragraph,
    extract_parties
)


@app.route("/api/search/keyword")
def search_keyword():
    """Full keyword search in citation, summary, and full_text."""

    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})

    keywords = q.split()

    keyword_filter = or_(
        LegalCitation.full_text.ilike(f"%{q}%"),
        LegalCitation.summary.ilike(f"%{keywords[0]}%"),
        LegalCitation.citation.ilike(f"%{keywords[0]}%"),
    )

    results = LegalCitation.query.filter(keyword_filter).limit(50).all()

    output = []
    for r in results:
        preview = extract_preview_paragraph(r.full_text)
        preview = highlight_keywords(preview, keywords)

        party_line = extract_parties(r.full_text, r.journal)

        output.append({
            "citation": r.citation,
            "court": r.court,
            "journal": r.journal,
            "party_line": party_line,
            "summary_preview": preview
        })

    return jsonify({
        "total": len(results),
        "results": output
    })
