#!/usr/bin/env python3
"""
KanoonPK - Professional Legal Research Platform
Replicating pakistanlawsite.com design with OpenAI integration
"""

import os
import openai
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
from models import db, User
from functools import wraps
from werkzeug.utils import secure_filename
from ocr_utils import ocr_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Flask secret key (required for sessions and CSRF)
app.secret_key = os.environ.get("SESSION_SECRET", "kanoonpk-dev-secret-2024")

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp', 'docx', 'doc', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure PostgreSQL Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Configure OpenAI with legacy API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin():
            flash('Admin access required', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

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

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('register'))
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(username=username, email=email, role='user')
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') == 'on'
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('login'))
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session.permanent = remember
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('home'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = User.query.get(session['user_id'])
    breadcrumbs = [{'text': 'My Profile', 'url': url_for('profile')}]
    return render_template('profile.html', user=user, breadcrumbs=breadcrumbs)

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    users = User.query.all()
    breadcrumbs = [{'text': 'Admin Dashboard', 'url': url_for('admin_dashboard')}]
    return render_template('admin.html', users=users, breadcrumbs=breadcrumbs)

# OCR Document Upload Route
@app.route('/upload-document', methods=['POST'])
def upload_document():
    """Upload and process document with OCR"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get file extension
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        # Extract text using OCR
        extracted_text, confidence = ocr_service.extract_text_from_file(filepath, file_ext)
        
        if extracted_text:
            return jsonify({
                'success': True,
                'filename': filename,
                'text': extracted_text,
                'confidence': confidence,
                'file_type': file_ext,
                'message': f'Successfully extracted text with {confidence:.1f}% confidence'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not extract text from document'
            }), 400
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/test-ocr')
def test_ocr_page():
    """Test page for OCR functionality"""
    return render_template('test_ocr.html')

# Export the Flask app
application = app

if __name__ == "__main__":
    print("🚀 Starting KanoonPK with Legacy OpenAI Integration...")
    app.run(host="0.0.0.0", port=5000, debug=True)