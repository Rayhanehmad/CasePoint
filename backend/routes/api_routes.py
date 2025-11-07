"""
Consolidated REST API routes for React frontend
All endpoints return JSON for frontend consumption
"""

from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
from models import db
from models.user import User
from models.case import LegalCitation
from routes.auth_routes import login_required
from services.utils_extract_parties import highlight_keywords, extract_preview_paragraph, extract_parties
import os
import logging
import re

api_bp = Blueprint('api', __name__)


# ==================== SEARCH API ====================

@api_bp.route('/search', methods=['GET', 'POST'])
def api_search():
    """
    Universal search endpoint for cases, acts, and statutes
    GET/POST /api/search?q=query&category=cases&year=2020&court=Supreme
    """
    if request.method == 'POST':
        data = request.get_json()
        query = data.get('query', '')
        category = data.get('category', 'all')
        filters = data.get('filters', {})
    else:
        query = request.args.get('q', '')
        category = request.args.get('category', 'all')
        filters = {
            'year': request.args.get('year'),
            'court': request.args.get('court'),
            'legal_area': request.args.get('legal_area'),
            'jurisdiction': request.args.get('jurisdiction'),
            'journal': request.args.get('journal')
        }
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    try:
        # Build filter conditions
        filter_conditions = []
        
        # Category filter
        if category == 'cases':
            filter_conditions.append(LegalCitation.document_type == 'case')
        elif category == 'acts':
            filter_conditions.append(LegalCitation.document_type.in_(['act', 'statute']))
        
        # Metadata filters
        if filters.get('year'):
            filter_conditions.append(LegalCitation.year == int(filters['year']))
        if filters.get('court'):
            filter_conditions.append(LegalCitation.court.ilike(f"%{filters['court']}%"))
        if filters.get('legal_area'):
            filter_conditions.append(LegalCitation.legal_area == filters['legal_area'])
        if filters.get('jurisdiction'):
            filter_conditions.append(LegalCitation.jurisdiction == filters['jurisdiction'])
        if filters.get('journal'):
            filter_conditions.append(LegalCitation.journal.ilike(f"%{filters['journal']}%"))
        
        # Text search conditions
        text_conditions = []
        if query:
            text_conditions = [
                LegalCitation.citation.ilike(f"%{query}%"),
                LegalCitation.title.ilike(f"%{query}%"),
                LegalCitation.summary.ilike(f"%{query}%"),
                LegalCitation.full_text.ilike(f"%{query}%"),
                LegalCitation.keywords.ilike(f"%{query}%")
            ]
        
        # Combine filters with text search
        if text_conditions and filter_conditions:
            search_query = LegalCitation.query.filter(
                and_(*filter_conditions, or_(*text_conditions))
            )
        elif text_conditions:
            search_query = LegalCitation.query.filter(or_(*text_conditions))
        elif filter_conditions:
            search_query = LegalCitation.query.filter(and_(*filter_conditions))
        else:
            search_query = LegalCitation.query
        
        # Paginate
        pagination = search_query.order_by(
            LegalCitation.year.desc(),
            LegalCitation.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'results': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        })
    
    except Exception as e:
        logging.error(f"Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/search/keyword', methods=['GET'])
def search_keyword():
    """
    Full keyword search in citation, summary, and full_text with highlighting and party extraction.
    GET /api/search/keyword?q=keywords
    Returns results with highlighted keywords, preview paragraphs, and party names.
    """
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"total": 0, "results": []})

    keywords = q.split()

    # Build keyword filter for multiple fields
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
            "id": r.id,
            "citation": r.citation,
            "court": r.court,
            "journal": r.journal,
            "year": r.year,
            "party_line": party_line,
            "summary_preview": preview
        })

    return jsonify({
        "total": len(results),
        "results": output
    })


# ==================== CASE API ====================

@api_bp.route('/case/<int:case_id>', methods=['GET'])
def api_get_case(case_id):
    """
    Get single case/citation details by ID
    GET /api/case/123
    """
    try:
        case = LegalCitation.query.get_or_404(case_id)
        
        # Find related cases
        related = LegalCitation.query.filter(
            LegalCitation.document_type == case.document_type,
            LegalCitation.legal_area == case.legal_area,
            LegalCitation.id != case.id
        ).limit(5).all()
        
        return jsonify({
            'success': True,
            'case': case.to_dict(),
            'related_cases': [c.to_dict() for c in related]
        })
    
    except Exception as e:
        logging.error(f"Error fetching case {case_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 404


@api_bp.route('/cases', methods=['GET'])
def api_list_cases():
    """
    List all cases with pagination and filtering
    GET /api/cases?page=1&per_page=20&court=Supreme
    """
    return api_search()  # Reuse search endpoint


# ==================== ACTS & STATUTES API ====================

@api_bp.route('/acts', methods=['GET'])
def api_list_acts():
    """
    List all acts and statutes
    GET /api/acts?q=search&page=1
    """
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    try:
        # Build query for acts/statutes
        acts_query = LegalCitation.query.filter(
            LegalCitation.document_type.in_(['act', 'statute'])
        )
        
        if query:
            acts_query = acts_query.filter(
                (LegalCitation.title.ilike(f'%{query}%')) |
                (LegalCitation.citation.ilike(f'%{query}%'))
            )
        
        pagination = acts_query.order_by(
            LegalCitation.title.asc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'acts': [act.to_dict() for act in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
    
    except Exception as e:
        logging.error(f"Error listing acts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== UPLOAD API ====================

@api_bp.route('/upload', methods=['POST'])
@login_required
def api_upload_document():
    """
    Upload legal document (PDF, DOCX, TXT)
    POST /api/upload with file in form-data
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Get form data
    document_type = request.form.get('document_type', 'case')
    title = request.form.get('title', '')
    
    try:
        from flask import current_app
        from services.ocr_service import extract_text_from_file
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text
        text_content = extract_text_from_file(filepath)
        
        if not text_content:
            return jsonify({
                'success': False,
                'error': 'Could not extract text from document'
            }), 400
        
        # Create citation record
        citation_text = f"Uploaded: {filename}"
        from services.utils import extract_journal_from_citation
        
        citation = LegalCitation(
            document_type=document_type,
            title=title or filename,
            citation=citation_text,
            journal=extract_journal_from_citation(citation_text),
            full_text=text_content[:10000],  # Limit text size
            summary=text_content[:500],
            file_path=filepath,
            file_type=filename.split('.')[-1].lower(),
            uploaded_by=session.get('user_id')
        )
        
        db.session.add(citation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Document uploaded successfully',
            'citation_id': citation.id,
            'citation': citation.to_dict()
        })
    
    except Exception as e:
        logging.error(f"Upload error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== USER DASHBOARD API ====================

@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def api_dashboard_stats():
    """
    Get dashboard statistics for logged-in user
    GET /api/dashboard/stats
    """
    try:
        user_id = session.get('user_id')
        
        # Get user's uploads
        user_uploads = LegalCitation.query.filter_by(uploaded_by=user_id).count()
        
        # Get total platform stats
        total_cases = LegalCitation.query.filter_by(document_type='case').count()
        total_acts = LegalCitation.query.filter(
            LegalCitation.document_type.in_(['act', 'statute'])
        ).count()
        total_citations = LegalCitation.query.count()
        
        return jsonify({
            'success': True,
            'stats': {
                'user_uploads': user_uploads,
                'total_cases': total_cases,
                'total_acts': total_acts,
                'total_citations': total_citations
            }
        })
    
    except Exception as e:
        logging.error(f"Dashboard stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/dashboard/recent', methods=['GET'])
@login_required
def api_recent_items():
    """
    Get recently uploaded items by user
    GET /api/dashboard/recent?limit=10
    """
    try:
        user_id = session.get('user_id')
        limit = request.args.get('limit', 10, type=int)
        
        recent = LegalCitation.query.filter_by(
            uploaded_by=user_id
        ).order_by(
            LegalCitation.created_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'recent_items': [item.to_dict() for item in recent]
        })
    
    except Exception as e:
        logging.error(f"Recent items error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== FILTERS & METADATA API ====================

@api_bp.route('/filters/courts', methods=['GET'])
def api_get_courts():
    """Get list of all unique courts"""
    try:
        courts = db.session.query(LegalCitation.court).filter(
            LegalCitation.court.isnot(None)
        ).distinct().all()
        
        return jsonify({
            'success': True,
            'courts': [c[0] for c in courts if c[0]]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/filters/legal-areas', methods=['GET'])
def api_get_legal_areas():
    """Get list of all legal areas"""
    try:
        areas = db.session.query(LegalCitation.legal_area).filter(
            LegalCitation.legal_area.isnot(None)
        ).distinct().all()
        
        return jsonify({
            'success': True,
            'legal_areas': [a[0] for a in areas if a[0]]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/filters/years', methods=['GET'])
def api_get_years():
    """Get list of all available years"""
    try:
        years = db.session.query(LegalCitation.year).filter(
            LegalCitation.year.isnot(None)
        ).distinct().order_by(LegalCitation.year.desc()).all()
        
        return jsonify({
            'success': True,
            'years': [y[0] for y in years if y[0]]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== TRACKING & ANALYTICS API ====================

@api_bp.route('/track_share/<string:citation>', methods=['GET', 'POST'])
def api_track_share(citation):
    """
    Track when a citation is shared
    GET/POST /api/track_share/2003 MLD 1075
    """
    from datetime import datetime
    try:
        c = LegalCitation.query.filter_by(citation=citation).first()
        if c:
            c.share_count = (c.share_count or 0) + 1
            c.last_shared = datetime.utcnow()
            db.session.commit()
            logging.info(f"Share tracked for citation: {citation}")
        return ('', 204)
    except Exception as e:
        logging.error(f"Error tracking share for {citation}: {e}")
        return ('', 500)


@api_bp.route('/track_embed/<string:citation>', methods=['GET', 'POST'])
def api_track_embed(citation):
    """
    Track when a citation is embedded
    GET/POST /api/track_embed/2003 MLD 1075
    """
    from datetime import datetime
    try:
        c = LegalCitation.query.filter_by(citation=citation).first()
        if c:
            c.embed_views = (c.embed_views or 0) + 1
            c.last_embedded = datetime.utcnow()
            db.session.commit()
            logging.info(f"Embed tracked for citation: {citation}")
        return ('', 204)
    except Exception as e:
        logging.error(f"Error tracking embed for {citation}: {e}")
        return ('', 500)


# ==================== AI CASE ANALYZER API ====================

@api_bp.route('/auto_counter_arguments', methods=['POST'])
def auto_counter_arguments():
    """
    Generate AI counter arguments from narrative text
    POST /api/auto_counter_arguments
    Body: {"text": "narrative"}
    """
    import openai
    try:
        data = request.get_json()
        if not data or not data.get('text'):
            return jsonify({'success': False, 'error': 'Text is required'}), 400
        
        text = data.get('text', '').strip()
        if len(text) < 10:
            return jsonify({'success': False, 'error': 'Text too short'}), 400
        
        # Check OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'OpenAI API key not configured'}), 500
        
        # Generate counter arguments using OpenAI
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert Pakistani legal defense attorney. Analyze the prosecution narrative and generate strong counter-arguments from a defense perspective. Be specific, cite legal principles, and suggest defenses under Pakistani law."},
                {"role": "user", "content": f"Prosecution narrative:\n\n{text}\n\nProvide detailed defense counter-arguments:"}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        counter_arguments = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'counter_arguments': counter_arguments
        })
    
    except Exception as e:
        logging.error(f"Error generating counter arguments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/analyze_case', methods=['POST'])
def analyze_case():
    """
    Analyze text to detect citations and statutes
    POST /api/analyze_case
    Body: {"text": "narrative"}
    Returns: {citations: [], statutes: []}
    """
    try:
        data = request.get_json()
        if not data or not data.get('text'):
            return jsonify({'success': False, 'error': 'Text is required'}), 400
        
        text = data.get('text', '').strip()
        
        # Detect citations using regex
        citation_patterns = [
            r'\b(PLD|SCMR|MLD|YLR|CLD|CLC|PTD|PCrLJ|PLC)\s+(\d{4})\s+([A-Za-z\s]+)\s+(\d+)\b',
            r'\b(\d{4})\s+(PLD|SCMR|MLD|YLR|CLD|CLC|PTD|PCrLJ|PLC)\s+(\d+)\b'
        ]
        
        detected_citations = []
        for pattern in citation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citation_text = match.group(0)
                # Try to find in database
                db_citation = LegalCitation.query.filter(
                    LegalCitation.citation.ilike(f'%{citation_text}%')
                ).first()
                
                if db_citation:
                    detected_citations.append({
                        'text': citation_text,
                        'id': db_citation.id,
                        'citation': db_citation.citation,
                        'court': db_citation.court,
                        'year': db_citation.year,
                        'is_database_item': True
                    })
                else:
                    detected_citations.append({
                        'text': citation_text,
                        'is_database_item': False
                    })
        
        # Detect statutes using regex
        statute_patterns = [
            r'\bSection\s+(\d+[A-Z]?)\b',
            r'\bArticle\s+(\d+[A-Z]?)\b',
            r'\b(PPC|CrPC|CPC|QSO)\s+(\d+[A-Z-]?)\b',
            r'\b([A-Z][A-Za-z\s]+Act\s+\d{4})\b',
            r'\b(Order\s+\d+\s+Rule\s+\d+)\b'
        ]
        
        detected_statutes = []
        for pattern in statute_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                statute_text = match.group(0)
                detected_statutes.append({
                    'text': statute_text,
                    'is_database_item': False  # Will auto-upgrade when LegalStatute DB exists
                })
        
        # Remove duplicates
        unique_citations = []
        seen_citation_texts = set()
        for cit in detected_citations:
            if cit['text'] not in seen_citation_texts:
                unique_citations.append(cit)
                seen_citation_texts.add(cit['text'])
        
        unique_statutes = []
        seen_statute_texts = set()
        for stat in detected_statutes:
            if stat['text'] not in seen_statute_texts:
                unique_statutes.append(stat)
                seen_statute_texts.add(stat['text'])
        
        return jsonify({
            'success': True,
            'citations': unique_citations,
            'statutes': unique_statutes
        })
    
    except Exception as e:
        logging.error(f"Error analyzing case: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/which_laws_apply', methods=['POST'])
def which_laws_apply():
    """
    Detect all applicable laws/sections from text
    POST /api/which_laws_apply
    Body: {"text": "narrative"}
    Returns: {laws: [{text, type, is_database_item}]}
    """
    try:
        data = request.get_json()
        if not data or not data.get('text'):
            return jsonify({'success': False, 'error': 'Text is required'}), 400
        
        text = data.get('text', '').strip()
        
        # Use same detection logic as analyze_case
        all_laws = []
        
        # Detect specific law types
        patterns = {
            'Section': r'\bSection\s+(\d+[A-Z]?)\b',
            'Article': r'\bArticle\s+(\d+[A-Z]?)\b',
            'PPC': r'\bPPC\s+(\d+[A-Z-]?)\b',
            'CrPC': r'\bCrPC\s+(\d+[A-Z-]?)\b',
            'CPC': r'\bCPC\s+(\d+[A-Z-]?)\b',
            'QSO': r'\bQSO\s+(\d+[A-Z-]?)\b',
            'Act': r'\b([A-Z][A-Za-z\s]+Act\s+\d{4})\b',
            'Order/Rule': r'\b(Order\s+\d+\s+Rule\s+\d+)\b'
        }
        
        for law_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                law_text = match.group(0)
                all_laws.append({
                    'text': law_text,
                    'type': law_type,
                    'is_database_item': False  # Auto-upgrade when DB exists
                })
        
        # Remove duplicates
        unique_laws = []
        seen = set()
        for law in all_laws:
            if law['text'] not in seen:
                unique_laws.append(law)
                seen.add(law['text'])
        
        return jsonify({
            'success': True,
            'laws': unique_laws,
            'total': len(unique_laws)
        })
    
    except Exception as e:
        logging.error(f"Error detecting laws: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
