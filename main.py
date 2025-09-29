#!/usr/bin/env python3
"""
KanoonPK - Professional Legal Research Platform
Replicating pakistanlawsite.com design with OpenAI integration
"""

import os
import openai
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Flask secret key (required for sessions and CSRF)
app.secret_key = os.environ.get("SESSION_SECRET", "kanoonpk-dev-secret-2024")

# Configure OpenAI with legacy API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Sample legal data for demonstration
SAMPLE_CASES = [
    {
        'title': 'Federation of Pakistan v. Gul Hassan Khan',
        'citation': 'PLD 1976 SC 57',
        'court': 'Supreme Court',
        'year': '1976',
        'snippet': 'Important case regarding constitutional principles and separation of powers...'
    },
    {
        'title': 'Malik Asad Ali v. Federation of Pakistan', 
        'citation': 'PLD 1998 SC 161',
        'court': 'Supreme Court',
        'year': '1998',
        'snippet': 'Landmark judgment on fundamental rights and judicial review...'
    }
]

SAMPLE_STATUTES = [
    {
        'title': 'Pakistan Penal Code, 1860',
        'citation': 'Act XLV of 1860',
        'type': 'Federal Statute',
        'year': '1860',
        'snippet': 'The main criminal law statute of Pakistan...'
    },
    {
        'title': 'Code of Civil Procedure, 1908',
        'citation': 'Act V of 1908', 
        'type': 'Federal Statute',
        'year': '1908',
        'snippet': 'Governs civil court procedures in Pakistan...'
    }
]

def generate_legal_analysis(query, context=""):
    """Generate AI-powered legal analysis using legacy OpenAI API"""
    if not openai.api_key:
        return "AI analysis requires OpenAI API key configuration. Please set OPENAI_API_KEY environment variable."
    
    try:
        # Create prompt for legal analysis
        if context:
            prompt = f"""As a legal research assistant specializing in Pakistan law, analyze the following query with the provided context:

Query: {query}

Context: {context}

Please provide:
1. A direct answer to the legal question
2. Relevant legal principles and precedents under Pakistan law
3. Citations to relevant statutes, cases, or legal authorities
4. Important considerations or limitations

Response should be professional and accurate."""
        else:
            prompt = f"""As a legal research assistant specializing in Pakistan law, provide a comprehensive analysis of the following legal query:

Query: {query}

Please provide:
1. A direct answer to the legal question
2. Relevant legal principles and precedents under Pakistan law
3. Citations to relevant statutes, cases, or legal authorities
4. Important considerations or limitations

Response should be professional and accurate."""
        
        # Use legacy OpenAI ChatCompletion API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert legal research assistant specializing in Pakistan law. Provide accurate, well-cited legal analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Legacy OpenAI API error: {e}")
        return f"AI analysis temporarily unavailable. Error: {str(e)}"

@app.route('/')
def home():
    """Homepage with search interface"""
    return render_template('home.html')

@app.route('/search/cases')
def search_cases():
    """Search cases page"""
    query = request.args.get('q', '')
    results = []
    
    if query:
        # Filter sample cases based on query
        results = [case for case in SAMPLE_CASES if query.lower() in case['title'].lower() or query.lower() in case['snippet'].lower()]
    
    breadcrumbs = [{'text': 'Cases', 'url': url_for('search_cases')}]
    return render_template('search_results.html', 
                         results=results, 
                         query=query, 
                         category='cases',
                         breadcrumbs=breadcrumbs)

@app.route('/search/statutes')
def search_statutes():
    """Search statutes page"""
    query = request.args.get('q', '')
    results = []
    
    if query:
        # Filter sample statutes based on query
        results = [statute for statute in SAMPLE_STATUTES if query.lower() in statute['title'].lower() or query.lower() in statute['snippet'].lower()]
    
    breadcrumbs = [{'text': 'Statutes & Acts', 'url': url_for('search_statutes')}]
    return render_template('search_results.html', 
                         results=results, 
                         query=query, 
                         category='statutes',
                         breadcrumbs=breadcrumbs)

@app.route('/search/rules')
def search_rules():
    """Search rules page"""
    query = request.args.get('q', '')
    breadcrumbs = [{'text': 'Rules', 'url': url_for('search_rules')}]
    return render_template('search_results.html', 
                         results=[], 
                         query=query, 
                         category='rules',
                         breadcrumbs=breadcrumbs)

@app.route('/search/results')
def search_results():
    """General search results page"""
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    
    results = []
    if query:
        if category == 'all' or category == 'cases':
            results.extend([{**case, 'type': 'case'} for case in SAMPLE_CASES if query.lower() in case['title'].lower() or query.lower() in case['snippet'].lower()])
        if category == 'all' or category == 'statutes':
            results.extend([{**statute, 'type': 'statute'} for statute in SAMPLE_STATUTES if query.lower() in statute['title'].lower() or query.lower() in statute['snippet'].lower()])
    
    breadcrumbs = [{'text': 'Search Results', 'url': url_for('search_results')}]
    return render_template('search_results.html', 
                         results=results, 
                         query=query, 
                         category=category,
                         breadcrumbs=breadcrumbs)

@app.route('/ai', methods=['GET', 'POST'])
def ai_analysis():
    """AI Analysis page with server-side rendering"""
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        context = request.form.get('context', '').strip()
        
        if not query:
            flash('Please enter a legal question', 'error')
            return redirect(url_for('ai_analysis'))
        
        # Generate AI analysis
        analysis = generate_legal_analysis(query, context)
        
        if analysis and "temporarily unavailable" not in analysis:
            return render_template('ai_analysis.html', 
                                 analysis=analysis, 
                                 query=query, 
                                 context=context,
                                 breadcrumbs=[{'text': 'AI Analysis', 'url': url_for('ai_analysis')}])
        else:
            flash(analysis or 'AI service unavailable', 'error')
            return redirect(url_for('ai_analysis'))
    
    # GET request - show the form
    breadcrumbs = [{'text': 'AI Analysis', 'url': url_for('ai_analysis')}]
    return render_template('ai_analysis.html', breadcrumbs=breadcrumbs)

@app.route('/api/analyze', methods=['POST'])
def analyze_legal_query():
    """Analyze legal query using legacy OpenAI API"""
    try:
        data = request.get_json()
        
        if not data or not data.get('query'):
            return jsonify({'error': 'Query is required'}), 400
        
        query = data.get('query', '')
        context = data.get('context', '')
        
        # Generate analysis using legacy OpenAI API
        analysis = generate_legal_analysis(query, context)
        
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

@app.route('/api/status')
def ai_status():
    """Check AI service status"""
    try:
        if not openai.api_key:
            return jsonify({
                'status': 'error',
                'service': 'legacy-openai',
                'message': 'OpenAI API key not configured'
            })
        
        # Test with a simple query
        test_result = generate_legal_analysis("Test connection", "")
        
        if test_result and "temporarily unavailable" not in test_result:
            return jsonify({
                'status': 'healthy',
                'service': 'legacy-openai',
                'message': 'AI service is operational'
            })
        else:
            return jsonify({
                'status': 'degraded',
                'service': 'legacy-openai',
                'message': 'AI service may be experiencing issues'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'service': 'legacy-openai',
            'message': f'AI service error: {str(e)}'
        })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'kanoonpk-openai',
        'version': '1.0.0'
    })

# Export the Flask app
application = app

if __name__ == "__main__":
    print("🚀 Starting KanoonPK with Legacy OpenAI Integration...")
    app.run(host="0.0.0.0", port=5000, debug=True)