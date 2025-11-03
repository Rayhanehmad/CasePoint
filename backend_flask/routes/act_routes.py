"""
Act routes - Search statutes, acts, and rules
"""

from flask import Blueprint, request, render_template, url_for, jsonify
from backend_flask.models import db, LegalCitation

act_bp = Blueprint('acts', __name__)


@act_bp.route('/statutes')
def search_statutes():
    """Search statutes and acts page"""
    query = request.args.get('q', '')
    year = request.args.get('year', '')
    
    # Build query for statutes and acts
    acts_query = LegalCitation.query.filter(
        LegalCitation.document_type.in_(['act', 'statute'])
    )
    
    if query:
        acts_query = acts_query.filter(
            (LegalCitation.title.ilike(f'%{query}%')) |
            (LegalCitation.citation.ilike(f'%{query}%')) |
            (LegalCitation.summary.ilike(f'%{query}%'))
        )
    
    if year:
        acts_query = acts_query.filter_by(year=int(year))
    
    results = acts_query.order_by(LegalCitation.year.desc()).all()
    
    breadcrumbs = [{'text': 'Statutes & Acts', 'url': url_for('acts.search_statutes')}]
    return render_template('search_results.html', 
                         results=results, 
                         query=query, 
                         category='statutes',
                         breadcrumbs=breadcrumbs)


@act_bp.route('/rules')
def search_rules():
    """Search rules page"""
    query = request.args.get('q', '')
    
    # Build query for rules
    rules_query = LegalCitation.query.filter_by(document_type='rule')
    
    if query:
        rules_query = rules_query.filter(
            (LegalCitation.title.ilike(f'%{query}%')) |
            (LegalCitation.citation.ilike(f'%{query}%')) |
            (LegalCitation.summary.ilike(f'%{query}%'))
        )
    
    results = rules_query.order_by(LegalCitation.year.desc()).all()
    
    breadcrumbs = [{'text': 'Rules', 'url': url_for('acts.search_rules')}]
    return render_template('search_results.html', 
                         results=results, 
                         query=query, 
                         category='rules',
                         breadcrumbs=breadcrumbs)


@act_bp.route('/<int:act_id>')
def act_detail(act_id):
    """View single act/statute/rule details"""
    act = LegalCitation.query.get_or_404(act_id)
    
    breadcrumbs = [
        {'text': 'Statutes & Acts', 'url': url_for('acts.search_statutes')},
        {'text': act.title, 'url': url_for('acts.act_detail', act_id=act.id)}
    ]
    
    return render_template('act_detail.html', 
                         act=act,
                         breadcrumbs=breadcrumbs)


# API Endpoints for React frontend

@act_bp.route('/api/acts', methods=['GET'])
def api_get_acts():
    """API endpoint to get all acts/statutes with filtering"""
    query = request.args.get('q', '')
    year = request.args.get('year', '')
    doc_type = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query
    if doc_type:
        acts_query = LegalCitation.query.filter_by(document_type=doc_type)
    else:
        acts_query = LegalCitation.query.filter(
            LegalCitation.document_type.in_(['act', 'statute', 'rule'])
        )
    
    if query:
        acts_query = acts_query.filter(
            (LegalCitation.title.ilike(f'%{query}%')) |
            (LegalCitation.citation.ilike(f'%{query}%')) |
            (LegalCitation.summary.ilike(f'%{query}%'))
        )
    
    if year:
        acts_query = acts_query.filter_by(year=int(year))
    
    # Paginate
    pagination = acts_query.order_by(LegalCitation.year.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'acts': [act.to_dict() for act in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@act_bp.route('/api/acts/<int:act_id>', methods=['GET'])
def api_get_act(act_id):
    """API endpoint to get single act/statute/rule"""
    act = LegalCitation.query.get_or_404(act_id)
    return jsonify({'act': act.to_dict()})
