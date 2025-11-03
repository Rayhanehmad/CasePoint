#!/usr/bin/env python3
"""
KanoonPK - Professional Legal Research Platform
Replicating pakistanlawsite.com design with OpenAI integration
"""

import os
import openai
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
from models import db, User, LegalCitation
from functools import wraps
from werkzeug.utils import secure_filename
from ocr_utils import ocr_service
import vector_search
import logging
from datetime import datetime, timedelta

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

# Track user activity
@app.before_request
def track_user_activity():
    """Update last_seen timestamp for logged-in users"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user.last_seen = datetime.utcnow()
            db.session.commit()

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

def generate_legal_analysis(query, context="", use_semantic_search=True):
    """Generate AI-powered legal analysis using legacy OpenAI API with ChromaDB semantic search"""
    if not openai.api_key:
        return "AI analysis requires OpenAI API key configuration. Please set OPENAI_API_KEY environment variable."
    
    try:
        # Search for relevant documents using ChromaDB if enabled
        relevant_docs = []
        if use_semantic_search:
            relevant_docs = vector_search.search_similar_documents(query, n_results=3)
        
        # Build context from relevant documents
        doc_context = ""
        if relevant_docs:
            doc_context = "\n\nRelevant Legal Documents:\n"
            for i, doc in enumerate(relevant_docs, 1):
                metadata = doc.get('metadata', {})
                doc_text = doc.get('text', '')[:500]  # First 500 chars
                doc_context += f"\n{i}. {metadata.get('title', 'Document')}"
                if metadata.get('citation'):
                    doc_context += f" ({metadata.get('citation')})"
                if metadata.get('court'):
                    doc_context += f" - {metadata.get('court')}"
                doc_context += f"\n   {doc_text}...\n"
        
        # Create prompt for legal analysis
        if context or doc_context:
            full_context = (context + doc_context) if context else doc_context
            prompt = f"""As a legal research assistant specializing in Pakistan law, analyze the following query with the provided context:

Query: {query}

Context: {full_context}

Please provide:
1. A direct answer to the legal question
2. Relevant legal principles and precedents under Pakistan law
3. Citations to relevant statutes, cases, or legal authorities from the context
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
                {"role": "system", "content": "You are an expert legal research assistant specializing in Pakistan law. Provide accurate, well-cited legal analysis based on the provided context."},
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
    from models import LegalCitation
    
    # Get recent citations (using id as fallback if created_at fails)
    try:
        recent_citations = LegalCitation.query.order_by(LegalCitation.created_at.desc()).limit(5).all()
    except Exception as e:
        print(f"Error ordering by created_at, using id instead: {e}")
        recent_citations = LegalCitation.query.order_by(LegalCitation.id.desc()).limit(5).all()
    
    total_citations = LegalCitation.query.count()
    
    return render_template('home.html', 
                         recent_citations=recent_citations,
                         total_citations=total_citations)

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

# Citation Management Routes
@app.route('/upload-citation', methods=['GET', 'POST'])
@admin_required
def upload_citation():
    """Upload single citation to database"""
    if request.method == 'POST':
        try:
            # Extract form data
            citation_data = {
                'document_type': request.form.get('document_type', 'case'),
                'title': request.form.get('title'),
                'citation': request.form.get('citation'),
                'court': request.form.get('court'),
                'jurisdiction': request.form.get('jurisdiction'),
                'date_decided': datetime.strptime(request.form.get('date_decided'), '%Y-%m-%d').date() if request.form.get('date_decided') else None,
                'year': int(request.form.get('year')) if request.form.get('year') else None,
                'legal_area': request.form.get('legal_area'),
                'case_type': request.form.get('case_type'),
                'judges': request.form.get('judges'),
                'summary': request.form.get('summary'),
                'full_text': request.form.get('full_text'),
                'headnotes': request.form.get('headnotes'),
                'keywords': request.form.get('keywords'),
                'citations_referred': request.form.get('citations_referred'),
                'statutes_referred': request.form.get('statutes_referred'),
                'uploaded_by': session['user_id']
            }
            
            # Create new citation
            citation = LegalCitation(**citation_data)
            db.session.add(citation)
            db.session.commit()
            
            flash(f'Citation {citation.citation} uploaded successfully!', 'success')
            return redirect(url_for('upload_citation'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading citation: {str(e)}', 'error')
            return redirect(url_for('upload_citation'))
    
    return render_template('upload_citation.html')

@app.route('/upload-citation-file', methods=['POST'])
@admin_required
def upload_citation_file():
    """Upload citation document file directly to database"""
    
    if 'file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('upload_citation'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('upload_citation'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get file extension
        file_ext = filename.rsplit('.', 1)[1].lower()
        file_size = os.path.getsize(filepath)
        
        # Extract text using OCR for supported file types
        extracted_text = None
        ocr_confidence = None
        
        if file_ext in ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'txt', 'docx']:
            logging.info(f"Extracting text from {filename} using OCR...")
            extracted_text, ocr_confidence = ocr_service.extract_text_from_file(filepath, file_ext)
            
            if extracted_text:
                logging.info(f"Successfully extracted {len(extracted_text)} characters with {ocr_confidence:.1f}% confidence")
            else:
                logging.warning(f"No text could be extracted from {filename}")
        
        # Store document with extracted text
        citation_data = {
            'document_type': request.form.get('document_type', 'case'),
            'title': request.form.get('title', filename.rsplit('.', 1)[0]),
            'citation': request.form.get('citation', filename),
            'court': request.form.get('court', ''),
            'jurisdiction': request.form.get('jurisdiction', ''),
            'year': int(request.form.get('year')) if request.form.get('year') else None,
            'legal_area': request.form.get('legal_area', ''),
            'summary': request.form.get('summary', ''),
            'file_path': filepath,
            'file_type': file_ext,
            'full_text': extracted_text,
            'ocr_confidence': ocr_confidence,
            'uploaded_by': session['user_id']
        }
        
        # Create citation
        citation = LegalCitation(**citation_data)
        db.session.add(citation)
        db.session.commit()
        
        # Add to vector database if text was extracted
        if extracted_text:
            metadata = {
                'document_type': citation_data.get('document_type', 'case'),
                'title': citation_data.get('title', ''),
                'citation': citation_data.get('citation', ''),
                'court': citation_data.get('court', ''),
                'legal_area': citation_data.get('legal_area', ''),
                'year': str(citation_data.get('year', ''))
            }
            
            # Add to ChromaDB
            vector_added = vector_search.add_document_to_vector_db(
                doc_id=str(citation.id),
                text=extracted_text,
                metadata=metadata
            )
            
            if vector_added:
                # Update citation with vector ID
                citation.vector_id = str(citation.id)
                db.session.commit()
                flash(f'Document "{filename}" uploaded, text extracted, and added to AI search successfully!', 'success')
            else:
                flash(f'Document "{filename}" uploaded and text extracted successfully!', 'success')
        else:
            flash(f'Document "{filename}" uploaded (text extraction unavailable)', 'warning')
        
        return redirect(url_for('view_citations'))
    
    flash('File type not allowed', 'error')
    return redirect(url_for('upload_citation'))

@app.route('/citations')
def view_citations():
    """View and search all citations - accessible to all users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_query = request.args.get('q', '').strip()
    
    # Build query
    query = LegalCitation.query
    
    # Apply search filters if query provided
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                LegalCitation.title.ilike(search_term),
                LegalCitation.citation.ilike(search_term),
                LegalCitation.court.ilike(search_term),
                LegalCitation.summary.ilike(search_term),
                LegalCitation.keywords.ilike(search_term)
            )
        )
    
    citations = query.order_by(LegalCitation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('citations.html', citations=citations, search_query=search_query)

@app.route('/citation/<int:id>')
def view_citation(id):
    """View single citation details"""
    citation = LegalCitation.query.get_or_404(id)
    return render_template('citation_detail.html', citation=citation)

@app.route('/download-citation/<int:id>')
def download_citation(id):
    """Download citation document file"""
    from flask import send_file
    citation = LegalCitation.query.get_or_404(id)
    
    if not citation.file_path or not os.path.exists(citation.file_path):
        flash('Document file not found', 'error')
        return redirect(url_for('view_citation', id=id))
    
    return send_file(citation.file_path, as_attachment=True)

@app.route('/preview-citation/<int:id>')
def preview_citation(id):
    """Preview citation document file in browser"""
    from flask import send_file
    import mimetypes
    
    citation = LegalCitation.query.get_or_404(id)
    
    if not citation.file_path or not os.path.exists(citation.file_path):
        flash('Document file not found', 'error')
        return redirect(url_for('view_citation', id=id))
    
    # Get the MIME type for the file
    mime_type, _ = mimetypes.guess_type(citation.file_path)
    
    # If it's a PDF, image, or text file, display inline
    if mime_type and (mime_type.startswith('image/') or mime_type == 'application/pdf' or mime_type.startswith('text/')):
        # Send file directly without X-Frame-Options to avoid Chrome blocking
        return send_file(
            citation.file_path, 
            mimetype=mime_type,
            as_attachment=False,
            download_name=None
        )
    
    # For other file types, download instead
    return send_file(citation.file_path, as_attachment=True)

@app.route('/compare-cases')
def compare_cases():
    """Compare multiple cases side by side"""
    # Get case IDs from query parameters
    case_ids_str = request.args.get('ids', '')
    
    if not case_ids_str:
        # If no IDs provided, show the selection page
        all_cases = LegalCitation.query.filter_by(document_type='case').order_by(LegalCitation.created_at.desc()).limit(50).all()
        return render_template('compare_select.html', cases=all_cases)
    
    # Parse comma-separated IDs
    try:
        case_ids = [int(id.strip()) for id in case_ids_str.split(',') if id.strip()]
    except ValueError:
        flash('Invalid case IDs provided', 'error')
        return redirect(url_for('compare_cases'))
    
    # Limit to maximum 3 cases for comparison
    if len(case_ids) > 3:
        flash('You can compare up to 3 cases at a time', 'warning')
        case_ids = case_ids[:3]
    
    if len(case_ids) < 2:
        flash('Please select at least 2 cases to compare', 'warning')
        return redirect(url_for('compare_cases'))
    
    # Fetch the cases
    cases = LegalCitation.query.filter(LegalCitation.id.in_(case_ids)).all()
    
    if len(cases) != len(case_ids):
        flash('Some cases could not be found', 'warning')
    
    return render_template('compare_cases.html', cases=cases)

@app.route('/citation/<int:id>/retry-ocr', methods=['POST'])
@admin_required
def retry_ocr(id):
    """Retry OCR text extraction for a citation document"""
    citation = LegalCitation.query.get_or_404(id)
    
    if not citation.file_path or not os.path.exists(citation.file_path):
        flash('Document file not found', 'error')
        return redirect(url_for('view_citation', id=id))
    
    try:
        # Extract text using OCR
        logging.info(f"Re-extracting text from citation ID {id}...")
        extracted_text, ocr_confidence = ocr_service.extract_text_from_file(
            citation.file_path, 
            citation.file_type or citation.file_path.rsplit('.', 1)[1].lower()
        )
        
        if extracted_text:
            citation.full_text = extracted_text
            citation.ocr_confidence = ocr_confidence
            db.session.commit()
            
            flash(f'Text extracted successfully! Confidence: {ocr_confidence:.1f}%', 'success')
            logging.info(f"Successfully extracted {len(extracted_text)} characters with {ocr_confidence:.1f}% confidence")
        else:
            flash('Could not extract text from this document', 'warning')
            logging.warning(f"Failed to extract text from citation ID {id}")
            
    except Exception as e:
        logging.error(f"OCR retry failed: {str(e)}")
        flash(f'Error during text extraction: {str(e)}', 'error')
    
    return redirect(url_for('view_citation', id=id))

# Admin Panel Routes
@app.route('/admin')
@admin_required
def admin_panel():
    """Admin panel with database management and statistics"""
    # Get statistics
    total_users = User.query.count()
    total_citations = LegalCitation.query.count()
    
    # Count online users (active in last 5 minutes)
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    online_users = User.query.filter(User.last_seen >= five_minutes_ago).count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Get recent citations
    recent_citations = LegalCitation.query.order_by(LegalCitation.created_at.desc()).limit(10).all()
    
    # Citations by legal area
    from sqlalchemy import func
    citations_by_area = db.session.query(
        LegalCitation.legal_area,
        func.count(LegalCitation.id).label('count')
    ).filter(LegalCitation.legal_area.isnot(None)).group_by(LegalCitation.legal_area).all()
    
    # Admin users count
    admin_count = User.query.filter(User.role == 'admin').count()
    regular_count = User.query.filter(User.role == 'user').count()
    
    return render_template('admin_panel.html',
        total_users=total_users,
        total_citations=total_citations,
        online_users=online_users,
        admin_count=admin_count,
        regular_count=regular_count,
        recent_users=recent_users,
        recent_citations=recent_citations,
        citations_by_area=citations_by_area
    )

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin page to view and manage all users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/citations')
@admin_required
def admin_citations():
    """Admin page to view and manage all citations"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    citations = LegalCitation.query.order_by(LegalCitation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin_citations.html', citations=citations)

@app.route('/admin/delete-citation/<int:id>', methods=['POST'])
@admin_required
def admin_delete_citation(id):
    """Delete a citation from database"""
    citation = LegalCitation.query.get_or_404(id)
    
    # Delete file if exists
    if citation.file_path and os.path.exists(citation.file_path):
        try:
            os.remove(citation.file_path)
        except:
            pass
    
    db.session.delete(citation)
    db.session.commit()
    
    flash(f'Citation "{citation.citation}" deleted successfully', 'success')
    return redirect(url_for('admin_citations'))

@app.route('/admin/delete-user/<int:id>', methods=['POST'])
@admin_required
def admin_delete_user(id):
    """Delete a user from database"""
    user = User.query.get_or_404(id)
    
    # Prevent deleting yourself
    if user.id == session['user_id']:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User "{user.username}" deleted successfully', 'success')
    return redirect(url_for('admin_users'))

# Export the Flask app
application = app

if __name__ == "__main__":
    print("🚀 Starting KanoonPK with Legacy OpenAI Integration...")
    app.run(host="0.0.0.0", port=5000, debug=True)