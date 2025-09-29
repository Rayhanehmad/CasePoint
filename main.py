#!/usr/bin/env python3
"""
KanoonPK SaaS - Flask Backend with Legacy OpenAI Integration
"""

import os
import openai
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure OpenAI with legacy API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Simple HTML template for the frontend
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KanoonPK - Legal Research with OpenAI</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            resize: vertical;
            min-height: 100px;
        }
        button {
            background: #667eea;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #5a6fd8;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
        .loading {
            text-align: center;
            color: #666;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            border-color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ KanoonPK Legal Research</h1>
        <p>AI-Powered Legal Analysis for Pakistan Law</p>
    </div>
    
    <div class="container">
        <form id="legalForm">
            <div class="form-group">
                <label for="query">Legal Question:</label>
                <textarea id="query" name="query" placeholder="Enter your legal question or case details..." required></textarea>
            </div>
            
            <div class="form-group">
                <label for="context">Legal Context (Optional):</label>
                <textarea id="context" name="context" placeholder="Provide any relevant case law, statutes, or legal documents..."></textarea>
            </div>
            
            <button type="submit" id="submitBtn">Analyze with AI</button>
        </form>
        
        <div id="result" style="display: none;"></div>
    </div>

    <script>
        document.getElementById('legalForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const resultDiv = document.getElementById('result');
            const query = document.getElementById('query').value;
            const context = document.getElementById('context').value;
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Analyzing...';
            resultDiv.style.display = 'block';
            resultDiv.className = 'result loading';
            resultDiv.innerHTML = '🤖 AI is analyzing your legal question...';
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        context: context
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    resultDiv.className = 'result';
                    resultDiv.innerHTML = '<h3>AI Legal Analysis:</h3><div>' + data.answer.replace(/\\n/g, '<br>') + '</div>';
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = '<h3>Error:</h3><div>' + data.error + '</div>';
                }
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = '<h3>Error:</h3><div>Failed to connect to AI service</div>';
            }
            
            // Reset button
            submitBtn.disabled = false;
            submitBtn.textContent = 'Analyze with AI';
        });
    </script>
</body>
</html>
"""

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
    """Main page with legal research interface"""
    return render_template_string(HTML_TEMPLATE)

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