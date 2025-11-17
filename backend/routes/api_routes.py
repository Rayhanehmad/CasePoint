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
from services.ai_service import generate_summary, generate_headnotes
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
    GET /api/search/keyword?q=keywords&location=court&years=5
    Returns results with highlighted keywords, preview paragraphs, and party names.
    Time filters: 5, 10, 15, 20 years or 'all'
    """
    from datetime import datetime
    
    q = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    years_filter = request.args.get("years", "all").strip()
    
    # At least one search parameter is required
    if not q and not location:
        return jsonify({"total": 0, "results": []})

    # Build filter conditions
    filter_conditions = []
    
    # Keyword filter for multiple fields - search full phrase across all fields
    if q:
        keyword_filter = or_(
            LegalCitation.title.ilike(f"%{q}%"),
            LegalCitation.citation.ilike(f"%{q}%"),
            LegalCitation.summary.ilike(f"%{q}%"),
            LegalCitation.full_text.ilike(f"%{q}%"),
            LegalCitation.headnotes.ilike(f"%{q}%"),
            LegalCitation.keywords.ilike(f"%{q}%"),
            LegalCitation.legal_area.ilike(f"%{q}%"),
            LegalCitation.ai_summary.ilike(f"%{q}%"),
            LegalCitation.ai_headnotes.ilike(f"%{q}%")
        )
        filter_conditions.append(keyword_filter)
    
    # Location/Court filter
    if location:
        location_filter = or_(
            LegalCitation.court.ilike(f"%{location}%"),
            LegalCitation.jurisdiction.ilike(f"%{location}%")
        )
        filter_conditions.append(location_filter)
    
    # Time filter based on years
    if years_filter != 'all':
        try:
            years_int = int(years_filter)
            current_year = datetime.now().year
            cutoff_year = current_year - years_int
            filter_conditions.append(LegalCitation.year >= cutoff_year)
        except ValueError:
            pass  # If years is not a valid number, skip time filter

    # Apply all filters
    if filter_conditions:
        query = LegalCitation.query.filter(and_(*filter_conditions))
    else:
        query = LegalCitation.query
    
    results = query.order_by(LegalCitation.year.desc()).limit(50).all()

    output = []
    for r in results:
        if q:
            keywords = q.split()
            preview = extract_preview_paragraph(r.full_text)
            preview = highlight_keywords(preview, keywords)
        else:
            preview = extract_preview_paragraph(r.full_text)

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


@api_bp.route('/search_citations', methods=['POST'])
def search_citations():
    """
    Citation-specific search endpoint with metadata fields
    POST /api/search_citations
    Fields: journal, year, page_no, court, judge, lawyer, parties
    """
    try:
        data = request.get_json() or {}
        
        # Build filter conditions based on provided fields
        filter_conditions = []
        
        # Journal filter
        if data.get('journal'):
            filter_conditions.append(LegalCitation.journal.ilike(f"%{data['journal']}%"))
        
        # Year filter
        if data.get('year'):
            try:
                filter_conditions.append(LegalCitation.year == int(data['year']))
            except (ValueError, TypeError):
                pass
        
        # Page number filter (search in citation field)
        if data.get('page_no'):
            filter_conditions.append(LegalCitation.citation.ilike(f"%{data['page_no']}%"))
        
        # Court filter
        if data.get('court'):
            filter_conditions.append(LegalCitation.court.ilike(f"%{data['court']}%"))
        
        # Judge filter (search in full text)
        if data.get('judge'):
            filter_conditions.append(LegalCitation.full_text.ilike(f"%{data['judge']}%"))
        
        # Lawyer filter (search in full text)
        if data.get('lawyer'):
            filter_conditions.append(LegalCitation.full_text.ilike(f"%{data['lawyer']}%"))
        
        # Parties filter (search in title and full text)
        if data.get('parties'):
            parties_filter = or_(
                LegalCitation.title.ilike(f"%{data['parties']}%"),
                LegalCitation.full_text.ilike(f"%{data['parties']}%")
            )
            filter_conditions.append(parties_filter)
        
        # Apply filters
        if filter_conditions:
            search_query = LegalCitation.query.filter(and_(*filter_conditions))
        else:
            search_query = LegalCitation.query
        
        # Get results
        results = search_query.order_by(
            LegalCitation.year.desc()
        ).limit(50).all()
        
        # Format results with party extraction
        output = []
        for r in results:
            party_line = extract_parties(r.full_text, r.journal)
            output.append({
                "id": r.id,
                "citation": r.citation,
                "title": r.title,
                "court": r.court,
                "journal": r.journal,
                "year": r.year,
                "summary": r.summary or "",
                "party_line": party_line,
                "legal_area": r.legal_area,
                "document_type": r.document_type
            })
        
        return jsonify({
            'success': True,
            'total': len(results),
            'results': output
        })
    
    except Exception as e:
        logging.error(f"Citation search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/advanced_search', methods=['POST'])
def advanced_search():
    """
    Advanced multi-field search endpoint with instant results
    POST /api/advanced_search
    Fields: court, judge, lawyer, parties, keywords, rules, acts, section
    """
    try:
        data = request.get_json() or {}
        
        # Build filter conditions
        filter_conditions = []
        
        # Court filter
        if data.get('court'):
            filter_conditions.append(LegalCitation.court.ilike(f"%{data['court']}%"))
        
        # Judge filter (full text search)
        if data.get('judge'):
            filter_conditions.append(LegalCitation.full_text.ilike(f"%{data['judge']}%"))
        
        # Lawyer filter (full text search)
        if data.get('lawyer'):
            filter_conditions.append(LegalCitation.full_text.ilike(f"%{data['lawyer']}%"))
        
        # Parties filter (title and full text)
        if data.get('parties'):
            parties_filter = or_(
                LegalCitation.title.ilike(f"%{data['parties']}%"),
                LegalCitation.full_text.ilike(f"%{data['parties']}%")
            )
            filter_conditions.append(parties_filter)
        
        # Keywords filter (search across multiple fields)
        if data.get('keywords'):
            keywords = data['keywords']
            keywords_filter = or_(
                LegalCitation.full_text.ilike(f"%{keywords}%"),
                LegalCitation.summary.ilike(f"%{keywords}%"),
                LegalCitation.keywords.ilike(f"%{keywords}%"),
                LegalCitation.title.ilike(f"%{keywords}%")
            )
            filter_conditions.append(keywords_filter)
        
        # Rules filter (full text search)
        if data.get('rules'):
            filter_conditions.append(LegalCitation.full_text.ilike(f"%{data['rules']}%"))
        
        # Acts filter (full text search)
        if data.get('acts'):
            filter_conditions.append(LegalCitation.full_text.ilike(f"%{data['acts']}%"))
        
        # Section filter (full text search)
        if data.get('section'):
            filter_conditions.append(LegalCitation.full_text.ilike(f"%{data['section']}%"))
        
        # Additional Acts filter (full text search)
        if data.get('acts2'):
            filter_conditions.append(LegalCitation.full_text.ilike(f"%{data['acts2']}%"))
        
        # Additional Section filter (full text search)
        if data.get('section2'):
            filter_conditions.append(LegalCitation.full_text.ilike(f"%{data['section2']}%"))
        
        # Apply filters
        if filter_conditions:
            search_query = LegalCitation.query.filter(and_(*filter_conditions))
        else:
            # If no filters, return empty results (don't return all citations)
            return jsonify({
                'success': True,
                'total': 0,
                'results': []
            })
        
        # Get results
        results = search_query.order_by(
            LegalCitation.year.desc(),
            LegalCitation.created_at.desc()
        ).limit(50).all()
        
        # Format results with party extraction
        output = []
        for r in results:
            party_line = extract_parties(r.full_text, r.journal)
            preview = extract_preview_paragraph(r.full_text) if r.full_text else ""
            
            output.append({
                "id": r.id,
                "citation": r.citation,
                "title": r.title,
                "court": r.court,
                "journal": r.journal,
                "year": r.year,
                "summary": r.summary or "",
                "preview": preview[:300] + "..." if len(preview) > 300 else preview,
                "party_line": party_line,
                "legal_area": r.legal_area,
                "jurisdiction": r.jurisdiction,
                "document_type": r.document_type
            })
        
        return jsonify({
            'success': True,
            'total': len(results),
            'results': output
        })
    
    except Exception as e:
        logging.error(f"Advanced search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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


# ==================== EXCERPT SHARING API ====================

@api_bp.route('/share_excerpt', methods=['POST'])
def share_excerpt():
    """
    Create a shareable excerpt from a citation
    POST /api/share_excerpt
    Body: {"citation_id": 123, "excerpt_text": "selected text", "notes": "optional"}
    """
    from models.shared_excerpt import SharedExcerpt
    from datetime import datetime
    
    try:
        # Check authentication
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        user_id = session['user_id']
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('citation_id') or not data.get('excerpt_text'):
            return jsonify({'success': False, 'error': 'citation_id and excerpt_text are required'}), 400
        
        citation_id = data.get('citation_id')
        excerpt_text = data.get('excerpt_text', '').strip()
        notes = data.get('notes', '').strip() or None
        
        # Validate excerpt length (50-1200 characters)
        if len(excerpt_text) < 50:
            return jsonify({'success': False, 'error': 'Excerpt must be at least 50 characters'}), 400
        if len(excerpt_text) > 1200:
            return jsonify({'success': False, 'error': 'Excerpt must be less than 1200 characters'}), 400
        
        # Check if citation exists and user has access
        citation = LegalCitation.query.get(citation_id)
        if not citation:
            return jsonify({'success': False, 'error': 'Citation not found'}), 404
        
        # Check daily quota (50 shares per user per day)
        from datetime import timedelta
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_count = SharedExcerpt.query.filter(
            SharedExcerpt.created_by == user_id,
            SharedExcerpt.created_at >= today_start
        ).count()
        
        if daily_count >= 50:
            return jsonify({'success': False, 'error': 'Daily share quota exceeded (50 per day)'}), 429
        
        # Create excerpt (with deduplication)
        excerpt = SharedExcerpt.create_excerpt(
            citation_id=citation_id,
            excerpt_text=excerpt_text,
            user_id=user_id,
            notes=notes,
            expiration_days=90
        )
        
        # Generate share URL
        share_url = url_for('api.get_shared_excerpt', share_code=excerpt.share_code, _external=True)
        
        # Update citation share count
        citation.share_count = (citation.share_count or 0) + 1
        citation.last_shared = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'share_code': excerpt.share_code,
            'share_url': share_url,
            'excerpt': excerpt.to_dict()
        })
    
    except Exception as e:
        logging.error(f"Error creating shared excerpt: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/shared/<string:share_code>', methods=['GET'])
def get_shared_excerpt(share_code):
    """
    Retrieve a shared excerpt (JSON API)
    GET /api/shared/<share_code>
    """
    from models.shared_excerpt import SharedExcerpt
    from datetime import datetime
    
    try:
        excerpt = SharedExcerpt.query.filter_by(share_code=share_code).first()
        
        if not excerpt:
            return jsonify({'success': False, 'error': 'Excerpt not found'}), 404
        
        # Check if excerpt is valid
        if not excerpt.is_valid():
            return jsonify({'success': False, 'error': 'Excerpt has expired or been revoked'}), 410
        
        # Increment view count (atomically within request context)
        excerpt.view_count += 1
        excerpt.last_viewed = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'excerpt': excerpt.to_dict()
        })
    
    except Exception as e:
        logging.error(f"Error retrieving shared excerpt: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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
        
        # Set API key for openai module (v0.28.x syntax)
        openai.api_key = api_key
        
        # Generate counter arguments using OpenAI (v0.28.x syntax)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert Pakistani legal defense attorney. Analyze the prosecution narrative and generate strong counter-arguments from a defense perspective. Be specific, cite legal principles, and suggest defenses under Pakistani law."},
                {"role": "user", "content": f"Prosecution narrative:\n\n{text}\n\nProvide detailed defense counter-arguments:"}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        counter_arguments = response['choices'][0]['message']['content']
        
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


# ==================== AI GENERATION API ====================

@api_bp.route('/generate_summary/<int:citation_id>', methods=['POST'])
def api_generate_summary(citation_id):
    """Generate AI summary for a citation (requires authentication)"""
    # Check authentication
    if not session.get('user_id'):
        logging.warning(f"Unauthorized access attempt to generate summary. Session: {dict(session)}")
        return jsonify({'error': 'Authentication required. Please log in to use AI features.'}), 401
    
    try:
        # Get citation from database
        citation = LegalCitation.query.get_or_404(citation_id)
        
        # Check if summary already exists
        if citation.ai_summary:
            logging.info(f"Returning cached AI summary for citation {citation_id}")
            return jsonify({
                'success': True,
                'summary': citation.ai_summary,
                'cached': True
            })
        
        # Check if full_text exists
        if not citation.full_text:
            return jsonify({'error': 'No full text available for this citation'}), 400
        
        # Generate summary
        logging.info(f"Generating AI summary for citation {citation_id}: {citation.citation}")
        summary = generate_summary(citation.full_text, citation.citation)
        
        if not summary:
            return jsonify({'error': 'Failed to generate summary. Please try again.'}), 500
        
        # Save summary to database
        citation.ai_summary = summary
        db.session.commit()
        
        logging.info(f"Successfully generated and saved AI summary for citation {citation_id}")
        
        return jsonify({
            'success': True,
            'summary': summary,
            'cached': False
        })
        
    except Exception as e:
        logging.error(f"Error generating summary for citation {citation_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@api_bp.route('/generate_headnotes/<int:citation_id>', methods=['POST'])
def api_generate_headnotes(citation_id):
    """Generate AI headnotes for a citation (requires authentication)"""
    # Check authentication
    if not session.get('user_id'):
        logging.warning(f"Unauthorized access attempt to generate headnotes. Session: {dict(session)}")
        return jsonify({'error': 'Authentication required. Please log in to use AI features.'}), 401
    
    try:
        # Get citation from database
        citation = LegalCitation.query.get_or_404(citation_id)
        
        # Check if headnotes already exist
        if citation.ai_headnotes:
            logging.info(f"Returning cached AI headnotes for citation {citation_id}")
            return jsonify({
                'success': True,
                'headnotes': citation.ai_headnotes,
                'cached': True
            })
        
        # Check if full_text exists
        if not citation.full_text:
            return jsonify({'error': 'No full text available for this citation'}), 400
        
        # Generate headnotes
        logging.info(f"Generating AI headnotes for citation {citation_id}: {citation.citation}")
        headnotes = generate_headnotes(citation.full_text, citation.citation)
        
        if not headnotes:
            return jsonify({'error': 'Failed to generate headnotes. Please try again.'}), 500
        
        # Save headnotes to database
        citation.ai_headnotes = headnotes
        db.session.commit()
        
        logging.info(f"Successfully generated and saved AI headnotes for citation {citation_id}")
        
        return jsonify({
            'success': True,
            'headnotes': headnotes,
            'cached': False
        })
        
    except Exception as e:
        logging.error(f"Error generating headnotes for citation {citation_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# ==================== USER PROFILE API ====================

@api_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def api_profile():
    """Get or update user profile"""
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None
            }
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        try:
            if 'username' in data and data['username']:
                user.username = data['username']
            if 'email' in data and data['email']:
                user.email = data['email']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_admin': user.is_admin
                }
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/upload_citation', methods=['POST'])
@login_required
def api_upload_citation():
    """
    Upload a legal citation with metadata and optional file
    POST /api/upload_citation
    """
    try:
        from services.ocr_service import extract_text_from_file
        from services.utils import extract_journal_from_citation
        
        citation_text = request.form.get('citation', '').strip()
        if not citation_text:
            return jsonify({'success': False, 'error': 'Citation is required'}), 400
        
        # Extract journal automatically
        journal = request.form.get('journal') or extract_journal_from_citation(citation_text)
        
        # Get file if provided
        full_text = request.form.get('summary', '')
        file_path = None
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(os.getcwd(), 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Extract text from file
                extracted_text = extract_text_from_file(file_path)
                if extracted_text:
                    full_text = extracted_text
        
        # Create citation
        citation = LegalCitation(
            citation=citation_text,
            court=request.form.get('court', ''),
            year=int(request.form.get('year')) if request.form.get('year') else None,
            journal=journal,
            page_no=request.form.get('page_no', ''),
            party_line=request.form.get('party_line', ''),
            legal_area=request.form.get('legal_area', ''),
            summary=request.form.get('summary', ''),
            headnotes=request.form.get('headnotes', ''),
            keywords=request.form.get('keywords', ''),
            full_text=full_text,
            file_path=file_path,
            uploaded_by=session.get('user_id'),
            document_type='case'
        )
        
        db.session.add(citation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Citation uploaded successfully',
            'citation_id': citation.id
        })
        
    except Exception as e:
        logging.error(f"Citation upload error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/upload_multi_pdf', methods=['POST'])
@login_required
def api_upload_multi_pdf():
    """
    Bulk upload multiple PDF files
    POST /api/upload_multi_pdf
    """
    try:
        from services.ocr_service import extract_text_from_file
        from services.utils import extract_journal_from_citation
        
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        successful = []
        failed = []
        upload_folder = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        for file in files:
            if not file.filename:
                continue
                
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Extract text
                text_content = extract_text_from_file(file_path)
                
                if not text_content:
                    failed.append(f"{filename}: Could not extract text")
                    continue
                
                # Use filename as citation
                citation_text = filename.replace('.pdf', '').replace('_', ' ')
                journal = extract_journal_from_citation(citation_text)
                
                citation = LegalCitation(
                    citation=citation_text,
                    journal=journal,
                    full_text=text_content,
                    summary=text_content[:500],
                    file_path=file_path,
                    file_type='pdf',
                    uploaded_by=session.get('user_id'),
                    document_type='case'
                )
                
                db.session.add(citation)
                successful.append(filename)
                
            except Exception as e:
                failed.append(f"{filename}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'results': {
                'successful': successful,
                'failed': failed,
                'summary': f"Uploaded {len(successful)} of {len(files)} files successfully"
            }
        })
        
    except Exception as e:
        logging.error(f"Multi-PDF upload error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/shared/<code>', methods=['GET'])
def api_get_shared_excerpt(code):
    """
    Get shared excerpt by code
    GET /api/shared/<code>
    """
    try:
        from models.shared_excerpt import SharedExcerpt
        from datetime import datetime
        
        excerpt = SharedExcerpt.query.filter_by(share_code=code).first()
        
        if not excerpt:
            return jsonify({'success': False, 'error': 'Excerpt not found'}), 404
        
        # Check if expired
        if excerpt.expires_at and excerpt.expires_at < datetime.utcnow():
            return jsonify({'success': False, 'error': 'This excerpt has expired'}), 410
        
        if excerpt.is_revoked:
            return jsonify({'success': False, 'error': 'This excerpt has been revoked'}), 403
        
        # Increment view count
        excerpt.view_count = (excerpt.view_count or 0) + 1
        db.session.commit()
        
        # Get citation details
        citation = LegalCitation.query.get(excerpt.citation_id)
        
        return jsonify({
            'success': True,
            'excerpt': {
                'excerpt_text': excerpt.excerpt_text,
                'citation': citation.citation if citation else '',
                'citation_id': excerpt.citation_id,
                'party_line': citation.party_line if citation else '',
                'court': citation.court if citation else '',
                'year': citation.year if citation else None,
                'journal': citation.journal if citation else '',
                'created_at': excerpt.created_at.isoformat() if excerpt.created_at else None,
                'view_count': excerpt.view_count
            }
        })
        
    except Exception as e:
        logging.error(f"Error retrieving shared excerpt: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
