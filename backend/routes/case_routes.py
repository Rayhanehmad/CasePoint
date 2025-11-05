"""
Case routes - Search cases, view details, compare cases
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from models import db
from models.case import LegalCitation
from routes.auth_routes import login_required
import qrcode
import io
import base64

case_bp = Blueprint('cases', __name__)


@case_bp.route('/search')
def search_cases():
    """Search cases page"""
    query = request.args.get('q', '')
    year = request.args.get('year', '')
    court = request.args.get('court', '')
    legal_area = request.args.get('legal_area', '')
    jurisdiction = request.args.get('jurisdiction', '')
    doc_type = request.args.get('type', '')
    
    # Build query - start with all legal citations
    cases_query = LegalCitation.query
    
    # Filter by document type if specified, otherwise default to cases
    if doc_type:
        cases_query = cases_query.filter_by(document_type=doc_type)
    else:
        cases_query = cases_query.filter_by(document_type='case')
    
    if query:
        cases_query = cases_query.filter(
            (LegalCitation.title.ilike(f'%{query}%')) |
            (LegalCitation.citation.ilike(f'%{query}%')) |
            (LegalCitation.summary.ilike(f'%{query}%'))
        )
    
    if year:
        cases_query = cases_query.filter_by(year=int(year))
    
    if court:
        cases_query = cases_query.filter_by(court=court)
    
    if legal_area:
        cases_query = cases_query.filter_by(legal_area=legal_area)
    
    if jurisdiction:
        cases_query = cases_query.filter_by(jurisdiction=jurisdiction)
    
    results = cases_query.order_by(LegalCitation.year.desc()).all()
    
    breadcrumbs = [{'text': 'Cases', 'url': url_for('cases.search_cases')}]
    return render_template('search_results.html', 
                         results=results, 
                         query=query, 
                         category='cases',
                         breadcrumbs=breadcrumbs)


@case_bp.route('/<int:case_id>')
def case_detail(case_id):
    """View single case details"""
    citation = LegalCitation.query.get_or_404(case_id)
    
    # Find related cases by legal area
    related_cases = LegalCitation.query.filter(
        LegalCitation.document_type == 'case',
        LegalCitation.legal_area == citation.legal_area,
        LegalCitation.id != citation.id
    ).limit(5).all()
    
    # Generate QR code for this citation
    citation_url = url_for('cases.case_detail', case_id=citation.id, _external=True)
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(citation_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    breadcrumbs = [
        {'text': 'Cases', 'url': url_for('cases.search_cases')},
        {'text': citation.citation, 'url': url_for('cases.case_detail', case_id=citation.id)}
    ]
    
    return render_template('citation_detail.html', 
                         citation=citation, 
                         related_cases=related_cases,
                         breadcrumbs=breadcrumbs,
                         qr_code=qr_code_base64)


@case_bp.route('/compare')
def compare_cases():
    """Compare multiple cases side by side"""
    case_ids = request.args.getlist('ids')
    
    cases = []
    if case_ids:
        for case_id in case_ids[:4]:  # Limit to 4 cases
            case = LegalCitation.query.get(int(case_id))
            if case:
                cases.append(case)
    
    breadcrumbs = [
        {'text': 'Cases', 'url': url_for('cases.search_cases')},
        {'text': 'Compare Cases', 'url': url_for('cases.compare_cases')}
    ]
    
    return render_template('compare_cases.html', 
                         cases=cases,
                         breadcrumbs=breadcrumbs)


# API Endpoints for React frontend

@case_bp.route('/api/cases', methods=['GET'])
def api_get_cases():
    """API endpoint to get all cases with filtering"""
    query = request.args.get('q', '')
    year = request.args.get('year', '')
    court = request.args.get('court', '')
    legal_area = request.args.get('legal_area', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query
    cases_query = LegalCitation.query.filter_by(document_type='case')
    
    if query:
        cases_query = cases_query.filter(
            (LegalCitation.title.ilike(f'%{query}%')) |
            (LegalCitation.citation.ilike(f'%{query}%')) |
            (LegalCitation.summary.ilike(f'%{query}%'))
        )
    
    if year:
        cases_query = cases_query.filter_by(year=int(year))
    
    if court:
        cases_query = cases_query.filter_by(court=court)
    
    if legal_area:
        cases_query = cases_query.filter_by(legal_area=legal_area)
    
    # Paginate
    pagination = cases_query.order_by(LegalCitation.year.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'cases': [case.to_dict() for case in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@case_bp.route('/api/cases/<int:case_id>', methods=['GET'])
def api_get_case(case_id):
    """API endpoint to get single case"""
    case = LegalCitation.query.get_or_404(case_id)
    
    # Find related cases
    related_cases = LegalCitation.query.filter(
        LegalCitation.document_type == 'case',
        LegalCitation.legal_area == case.legal_area,
        LegalCitation.id != case.id
    ).limit(5).all()
    
    return jsonify({
        'case': case.to_dict(),
        'related_cases': [c.to_dict() for c in related_cases]
    })
