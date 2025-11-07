"""
AI routes - Legal analysis and AI-powered search
"""

from flask import Blueprint, request, render_template, url_for, jsonify, flash, redirect
from services import generate_legal_analysis

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/analysis', methods=['GET', 'POST'])
def ai_analysis():
    """AI Analysis page with server-side rendering"""
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        context = request.form.get('context', '').strip()
        
        if not query:
            flash('Please enter a legal question', 'error')
            return redirect(url_for('ai.ai_analysis'))
        
        # Generate AI analysis
        analysis = generate_legal_analysis(query, context)
        
        if analysis and "temporarily unavailable" not in analysis:
            return render_template('ai_analysis.html', 
                                 analysis=analysis, 
                                 query=query, 
                                 context=context,
                                 breadcrumbs=[{'text': 'AI Analysis', 'url': url_for('ai.ai_analysis')}])
        else:
            flash(analysis or 'AI service unavailable', 'error')
            return redirect(url_for('ai.ai_analysis'))
    
    # GET request - show the form
    breadcrumbs = [{'text': 'AI Analysis', 'url': url_for('ai.ai_analysis')}]
    return render_template('ai_analysis.html', breadcrumbs=breadcrumbs)


# API Endpoints for React frontend

@ai_bp.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for AI legal analysis"""
    try:
        data = request.get_json()
        
        if not data or not data.get('query'):
            return jsonify({'error': 'Query is required'}), 400
        
        query = data.get('query', '')
        context = data.get('context', '')
        use_semantic_search = data.get('use_semantic_search', True)
        
        # Generate analysis
        analysis = generate_legal_analysis(query, context, use_semantic_search)
        
        if analysis and "temporarily unavailable" not in analysis:
            return jsonify({
                'answer': analysis,
                'query': query,
                'status': 'success'
            })
        else:
            return jsonify({'error': analysis or 'AI service unavailable'}), 503
        
    except Exception as e:
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500


@ai_bp.route('/api/status', methods=['GET'])
def api_status():
    """Check AI service status"""
    import os
    import openai
    
    try:
        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({
                'status': 'error',
                'service': 'openai',
                'message': 'OpenAI API key not configured'
            })
        
        return jsonify({
            'status': 'healthy',
            'service': 'openai',
            'message': 'AI service is operational'
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'service': 'openai',
            'message': f'AI service error: {str(e)}'
        })


@ai_bp.route('/case-analyzer', methods=['GET'])
def case_analyzer():
    """AI Case Analyzer page"""
    breadcrumbs = [{'text': 'AI Case Analyzer', 'url': url_for('ai.case_analyzer')}]
    return render_template('case_analyzer.html', breadcrumbs=breadcrumbs)
