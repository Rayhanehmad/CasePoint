"""
AI routes - Legal analysis and AI-powered search
"""

from flask import Blueprint, request, render_template, url_for, jsonify, flash, redirect, session
from services import generate_legal_analysis
from services.ai_service import generate_summary, generate_headnotes
from models import db
from models.case import LegalCitation
import logging

logger = logging.getLogger(__name__)

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


@ai_bp.route('/api/generate_citation', methods=['POST'])
def api_generate_citation():
    """API endpoint for AI-powered citation generation"""
    import openai
    import os
    
    try:
        data = request.get_json()
        
        if not data or not data.get('case_details'):
            return jsonify({'error': 'Case details are required'}), 400
        
        case_details = data.get('case_details', '')
        citation_type = data.get('citation_type', 'case')
        jurisdiction = data.get('jurisdiction', 'Pakistan')
        
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({'error': 'AI service not configured'}), 503
        
        # Build prompt for citation generation
        prompt = f"""You are a legal citation expert specializing in Pakistan law. Generate a properly formatted legal citation based on the following details.

Citation Type: {citation_type}
Jurisdiction: {jurisdiction}
Case Details:
{case_details}

Please provide:
1. A properly formatted citation following Pakistan legal citation standards
2. Break down the citation into its components (parties, year, court, journal, page number, etc.)
3. Any notes or clarifications about the citation format

Format your response as JSON with the following structure:
{{
    "formatted_citation": "The complete formatted citation string",
    "components": {{
        "parties": "Party names",
        "year": "Year",
        "court": "Court name",
        "journal": "Journal abbreviation (if applicable)",
        "page": "Page number (if applicable)",
        "citation_number": "Citation number (if applicable)"
    }},
    "notes": "Any important notes about the citation format or missing information"
}}

If information is missing or unclear, make reasonable assumptions based on Pakistan legal standards and note them."""

        # Call OpenAI API (legacy format)
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in Pakistan legal citation formats and standards."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Parse the AI response
        ai_response = response['choices'][0]['message']['content'].strip()
        
        # Try to extract JSON from the response
        import json
        import re
        
        # Look for JSON in the response
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            citation_data = json.loads(json_match.group())
        else:
            # Fallback if no JSON found
            citation_data = {
                "formatted_citation": ai_response,
                "components": {},
                "notes": "Generated citation may need manual verification"
            }
        
        return jsonify({
            'success': True,
            'citation': citation_data
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return jsonify({
            'success': True,
            'citation': {
                "formatted_citation": ai_response if 'ai_response' in locals() else "Error generating citation",
                "components": {},
                "notes": "Could not parse structured citation data. Please verify the format."
            }
        })
    except Exception as e:
        logger.error(f"Citation generation error: {e}")
        return jsonify({'error': f'Citation generation failed: {str(e)}'}), 500


@ai_bp.route('/case-analyzer', methods=['GET'])
def case_analyzer():
    """AI Case Analyzer page"""
    breadcrumbs = [{'text': 'AI Case Analyzer', 'url': url_for('ai.case_analyzer')}]
    return render_template('case_analyzer.html', breadcrumbs=breadcrumbs)


@ai_bp.route('/api/generate_summary/<int:citation_id>', methods=['POST'])
def api_generate_summary(citation_id):
    """Generate AI summary for a citation (requires authentication)"""
    # Check authentication
    if not session.get('user_id'):
        logger.warning(f"Unauthorized access attempt to generate summary. Session: {dict(session)}")
        return jsonify({'error': 'Authentication required. Please log in to use AI features.'}), 401
    
    try:
        # Get citation from database
        citation = LegalCitation.query.get_or_404(citation_id)
        
        # Check if summary already exists
        if citation.ai_summary:
            logger.info(f"Returning cached AI summary for citation {citation_id}")
            return jsonify({
                'success': True,
                'summary': citation.ai_summary,
                'cached': True
            })
        
        # Check if full_text exists
        if not citation.full_text:
            return jsonify({'error': 'No full text available for this citation'}), 400
        
        # Generate summary
        logger.info(f"Generating AI summary for citation {citation_id}: {citation.citation}")
        summary = generate_summary(citation.full_text, citation.citation)
        
        if not summary:
            return jsonify({'error': 'Failed to generate summary. Please try again.'}), 500
        
        # Save summary to database
        citation.ai_summary = summary
        db.session.commit()
        
        logger.info(f"Successfully generated and saved AI summary for citation {citation_id}")
        
        return jsonify({
            'success': True,
            'summary': summary,
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"Error generating summary for citation {citation_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@ai_bp.route('/api/generate_headnotes/<int:citation_id>', methods=['POST'])
def api_generate_headnotes(citation_id):
    """Generate AI headnotes for a citation (requires authentication)"""
    # Check authentication
    if not session.get('user_id'):
        logger.warning(f"Unauthorized access attempt to generate headnotes. Session: {dict(session)}")
        return jsonify({'error': 'Authentication required. Please log in to use AI features.'}), 401
    
    try:
        # Get citation from database
        citation = LegalCitation.query.get_or_404(citation_id)
        
        # Check if headnotes already exist
        if citation.ai_headnotes:
            logger.info(f"Returning cached AI headnotes for citation {citation_id}")
            return jsonify({
                'success': True,
                'headnotes': citation.ai_headnotes,
                'cached': True
            })
        
        # Check if full_text exists
        if not citation.full_text:
            return jsonify({'error': 'No full text available for this citation'}), 400
        
        # Generate headnotes
        logger.info(f"Generating AI headnotes for citation {citation_id}: {citation.citation}")
        headnotes = generate_headnotes(citation.full_text, citation.citation)
        
        if not headnotes:
            return jsonify({'error': 'Failed to generate headnotes. Please try again.'}), 500
        
        # Save headnotes to database
        citation.ai_headnotes = headnotes
        db.session.commit()
        
        logger.info(f"Successfully generated and saved AI headnotes for citation {citation_id}")
        
        return jsonify({
            'success': True,
            'headnotes': headnotes,
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"Error generating headnotes for citation {citation_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
