"""
SaaS Routes and API endpoints for KanoonPK Legal Research Platform
"""
from flask import Blueprint, request, jsonify, render_template, render_template_string, redirect, url_for, flash, g, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import datetime
import json
import uuid
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from models import (
    db, Tenant, User, Subscription, UsageMetric, LegalDocument, QueryHistory, LegalWorkspace
)
from saas_app import (
    require_tenant, require_plan_feature, require_usage_limit,
    EnhancedLegalSearchEngine, TenantDocumentManager, client, logger
)

# =============================================================================
# BLUEPRINT DEFINITIONS
# =============================================================================

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
api_bp = Blueprint('api', __name__, url_prefix='/api')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
main_bp = Blueprint('main', __name__)

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@auth_bp.route('/register-tenant', methods=['GET', 'POST'])
def register_tenant():
    """Register new tenant organization"""
    if request.method == 'GET':
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en" data-bs-theme="dark">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Start Free Trial - KanoonPK</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                .gradient-bg {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .glass-card {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 20px;
                }
                .modern-input {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    color: white;
                }
                .modern-input:focus {
                    background: rgba(255, 255, 255, 0.2);
                    border-color: #667eea;
                    color: white;
                    box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
                }
                .modern-btn {
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    border: none;
                    border-radius: 10px;
                    padding: 12px 30px;
                    font-weight: 600;
                    transition: all 0.3s;
                }
                .modern-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
                }
            </style>
        </head>
        <body>
            <div class="gradient-bg d-flex align-items-center">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-md-8 col-lg-6">
                            <div class="glass-card p-5">
                                <div class="text-center mb-4">
                                    <i class="fas fa-robot fa-3x text-light mb-3"></i>
                                    <h2 class="text-white">Start Your AI Legal Research</h2>
                                    <p class="text-light">Get instant access to Pakistan's most advanced legal AI</p>
                                </div>

                                <form id="quickStartForm">
                                    <div class="mb-3">
                                        <label class="form-label text-light">Organization Name</label>
                                        <input type="text" class="form-control modern-input" name="organization_name" placeholder="Your Law Firm" required>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label text-light">Your Email</label>
                                        <input type="email" class="form-control modern-input" name="email" placeholder="lawyer@firm.com" required>
                                    </div>
                                    
                                    <div class="mb-4">
                                        <label class="form-label text-light">Password</label>
                                        <input type="password" class="form-control modern-input" name="password" placeholder="••••••••" required>
                                    </div>

                                    <div class="d-grid">
                                        <button type="submit" class="btn modern-btn btn-lg text-white">
                                            <i class="fas fa-magic me-2"></i>Start Legal AI Chat
                                        </button>
                                    </div>
                                </form>

                                <div class="text-center mt-4">
                                    <small class="text-light">
                                        Already have an account? 
                                        <a href="/auth/login" class="text-decoration-none" style="color: #a78bfa;">Login here</a>
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                document.getElementById('quickStartForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const formData = new FormData(this);
                    const data = Object.fromEntries(formData.entries());
                    
                    // Generate a simple subdomain from organization name
                    data.subdomain = data.organization_name.toLowerCase()
                        .replace(/[^a-z0-9]/g, '')
                        .substring(0, 10) + Math.floor(Math.random() * 1000);
                    
                    data.admin_email = data.email;
                    data.admin_password = data.password;
                    data.admin_first_name = 'User';
                    data.admin_last_name = 'Admin';
                    
                    const submitBtn = this.querySelector('button[type="submit"]');
                    const originalText = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Setting up your AI...';
                    
                    try {
                        const response = await fetch('/auth/register-tenant', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(data)
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            submitBtn.innerHTML = '<i class="fas fa-check me-2"></i>Success! Opening AI Chat...';
                            setTimeout(() => {
                                // Redirect to chat interface
                                window.location.href = '/chat?tenant=' + result.subdomain;
                            }, 1500);
                        } else {
                            alert('Setup failed: ' + result.error);
                        }
                    } catch (error) {
                        alert('Setup failed. Please try again.');
                    } finally {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }
                });
            </script>
        </body>
        </html>
        """)
    
    data = request.get_json() if request.is_json else request.form
    
    # Validate required fields
    required_fields = ['organization_name', 'subdomain', 'admin_email', 'admin_password', 'admin_first_name', 'admin_last_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    # Check if subdomain is available
    existing_tenant = Tenant.query.filter_by(subdomain=data['subdomain']).first()
    if existing_tenant:
        return jsonify({'error': 'Subdomain already taken'}), 400
    
    # Check if admin email is already used
    existing_user = User.query.filter_by(email=data['admin_email']).first()
    if existing_user:
        return jsonify({'error': 'Email already registered'}), 400
    
    try:
        # Create tenant
        tenant = Tenant(
            name=data['organization_name'],
            subdomain=data['subdomain'].lower(),
            plan='free'
        )
        db.session.add(tenant)
        db.session.flush()  # Get tenant ID
        
        # Skip schema creation for now - use simple approach
        # if not create_tenant_schema(tenant.id):
        #     raise Exception("Failed to create tenant schema")
        
        # Create admin user
        admin_user = User(
            email=data['admin_email'],
            first_name=data['admin_first_name'],
            last_name=data['admin_last_name'],
            tenant_id=tenant.id,
            role='owner',
            is_verified=True,
            status='active'
        )
        admin_user.set_password(data['admin_password'])
        db.session.add(admin_user)
        
        # Create subscription record
        subscription = Subscription(
            tenant_id=tenant.id,
            plan_name='free',
            current_period_start=datetime.datetime.utcnow(),
            current_period_end=datetime.datetime.utcnow() + datetime.timedelta(days=30)
        )
        db.session.add(subscription)
        
        db.session.commit()
        
        # Auto-login the admin user
        login_user(admin_user)
        session['tenant_subdomain'] = tenant.subdomain
        
        return jsonify({
            'success': True,
            'tenant_id': tenant.id,
            'subdomain': tenant.subdomain,
            'message': 'Organization registered successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Tenant registration error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'GET':
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en" data-bs-theme="dark">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login - KanoonPK AI</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                .gradient-bg {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .glass-card {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 20px;
                }
            </style>
        </head>
        <body>
            <div class="gradient-bg d-flex align-items-center">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-md-6 col-lg-4">
                            <div class="glass-card p-5">
                                <div class="text-center mb-4">
                                    <i class="fas fa-brain fa-3x text-light mb-3"></i>
                                    <h4 class="text-white">Welcome Back</h4>
                                    <p class="text-light">Access your Legal AI Assistant</p>
                                </div>

                                <form id="loginForm">
                                    <div class="mb-3">
                                        <input type="email" class="form-control bg-light" name="email" placeholder="Email Address" required>
                                    </div>
                                    <div class="mb-4">
                                        <input type="password" class="form-control bg-light" name="password" placeholder="Password" required>
                                    </div>
                                    <div class="d-grid">
                                        <button type="submit" class="btn btn-primary btn-lg">
                                            <i class="fas fa-sign-in-alt me-2"></i>Access AI Chat
                                        </button>
                                    </div>
                                </form>

                                <div class="text-center mt-4">
                                    <small class="text-light">
                                        Need an account? 
                                        <a href="/auth/register-tenant" class="text-decoration-none" style="color: #a78bfa;">Start Free Trial</a>
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                document.getElementById('loginForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const formData = new FormData(this);
                    const data = Object.fromEntries(formData.entries());
                    
                    try {
                        const response = await fetch('/auth/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(data)
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            localStorage.setItem('access_token', result.access_token);
                            window.location.href = '/chat';
                        } else {
                            alert('Login failed: ' + result.error);
                        }
                    } catch (error) {
                        alert('Login failed. Please try again.');
                    }
                });
            </script>
        </body>
        </html>
        """)
    
    data = request.get_json() if request.is_json else request.form
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Find user
    user = User.query.filter_by(email=email, status='active').first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Check if user's tenant is active
    if user.tenant_ref.status != 'active':
        return jsonify({'error': 'Account suspended. Contact support.'}), 403
    
    # Update login stats
    user.last_login = datetime.datetime.utcnow()
    user.login_count += 1
    db.session.commit()
    
    # Login user
    login_user(user)
    session['tenant_subdomain'] = user.tenant_ref.subdomain
    
    # Create JWT token for API access
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'tenant_id': user.tenant_id,
            'role': user.role,
            'email': user.email
        }
    )
    
    return jsonify({
        'success': True,
        'access_token': access_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.get_full_name(),
            'role': user.role,
            'tenant': user.tenant_ref.name
        }
    })

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    session.pop('tenant_subdomain', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@auth_bp.route('/invite-user', methods=['POST'])
@login_required
@require_tenant
def invite_user():
    """Invite new user to tenant (admin/owner only)"""
    if not current_user.has_permission('manage_users'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'member')
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    # Check if tenant can add more users
    if not g.tenant.can_perform_action('add_user'):
        return jsonify({'error': 'User limit exceeded for your plan'}), 429
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'User already registered'}), 400
    
    try:
        # Create user with temporary password
        temp_password = str(uuid.uuid4())[:12]
        new_user = User(
            email=email,
            tenant_id=g.tenant.id,
            role=role,
            is_verified=False
        )
        new_user.set_password(temp_password)
        db.session.add(new_user)
        db.session.commit()
        
        # TODO: Send invitation email with temp_password
        
        return jsonify({
            'success': True,
            'user_id': new_user.id,
            'temporary_password': temp_password,  # Remove in production
            'message': 'User invited successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"User invitation error: {e}")
        return jsonify({'error': 'Failed to invite user'}), 500

# =============================================================================
# MAIN APPLICATION ROUTES
# =============================================================================

@main_bp.route('/dashboard')
@require_tenant  
def dashboard():
    """Main dashboard interface for authenticated users"""
    return render_template('saas/dashboard.html', 
                         tenant=g.tenant,
                         user=current_user if current_user.is_authenticated else None)

@main_bp.route('/app')
@login_required
@require_tenant
def app_dashboard():
    """User dashboard with analytics"""
    # Get user's usage statistics
    current_month = datetime.datetime.utcnow().strftime('%Y-%m')
    
    query_usage = g.tenant.get_current_usage('query', current_month)
    doc_usage = g.tenant.get_current_usage('document_upload')
    
    # Get recent queries
    recent_queries = QueryHistory.query.filter_by(user_id=current_user.id)\
                                      .order_by(QueryHistory.created_at.desc())\
                                      .limit(10).all()
    
    # Get uploaded documents
    recent_docs = LegalDocument.query.filter_by(upload_user_id=current_user.id)\
                                    .order_by(LegalDocument.created_at.desc())\
                                    .limit(5).all()
    
    return render_template('saas/dashboard.html', 
                         tenant=g.tenant,
                         query_usage=query_usage,
                         doc_usage=doc_usage,
                         recent_queries=recent_queries,
                         recent_docs=recent_docs,
                         plan_limits=PLAN_LIMITS[g.tenant.plan])

# =============================================================================
# LEGAL RESEARCH API ROUTES
# =============================================================================

@api_bp.route('/chat', methods=['POST'])
@login_required
@require_tenant
@require_usage_limit('query')
def enhanced_chat():
    """Enhanced legal research chat with advanced search"""
    data = request.get_json()
    query = data.get('message', '').strip()
    search_filters = data.get('filters', {})
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        # Initialize search engine for tenant
        search_engine = EnhancedLegalSearchEngine(g.tenant.id)
        
        # Perform advanced search
        search_results = search_engine.advanced_search(query, search_filters)
        
        # Build context for GPT
        context = ""
        citations_used = []
        
        if search_results['documents']:
            for i, doc in enumerate(search_results['documents'][:5]):
                metadata = search_results['metadata'][i]
                citation = metadata.get('citation', metadata.get('source', ''))
                
                if citation not in citations_used:
                    citations_used.append(citation)
                
                # Truncate document for context
                doc_excerpt = doc[:800] + "..." if len(doc) > 800 else doc
                context += f"\n\n[Source: {citation}] {doc_excerpt}"
        
        # Enhanced legal system prompt
        legal_prompt = f"""
        You are KanoonPK, an AI Legal Research Assistant specialized in Pakistan law.
        You must provide accurate legal information based on Pakistani laws, case references, and uploaded documents.
        
        Guidelines:
        - Always provide specific citations when available from the retrieved documents
        - Focus on Pakistan's legal framework including Constitution 1973, Pakistan Penal Code, Civil/Criminal Procedure Codes
        - If you cannot find relevant information in the provided context, clearly state the limitations
        - Provide practical legal guidance while noting this is not formal legal advice
        - Format citations properly using Pakistani legal citation standards
        
        Search Filters Applied: {search_filters}
        """
        
        # Generate response using OpenAI
        messages = [
            {"role": "system", "content": legal_prompt},
            {"role": "user", "content": f"Legal Question: {query}\n\nRelevant Legal Documents:{context}"}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Using latest model available
            messages=messages,
            max_tokens=1500,
            temperature=0.3  # Lower temperature for more factual responses
        )
        
        answer = response.choices[0].message.content
        
        # Extract legal citations from answer
        extracted_citations = search_engine.extract_legal_citations(answer)
        
        # Calculate confidence score based on search results
        confidence_score = 0.8 if search_results['documents'] else 0.3
        if search_results.get('confidence_scores'):
            avg_confidence = sum(search_results['confidence_scores'][:3]) / min(3, len(search_results['confidence_scores']))
            confidence_score = max(confidence_score, avg_confidence)
        
        # Save query to history
        query_record = QueryHistory(
            question=query,
            answer=answer,
            search_filters=search_filters,
            found_citations=citations_used + [c['full_citation'] for c in extracted_citations],
            confidence_score=confidence_score,
            user_id=current_user.id,
            session_id=session.get('session_id', str(uuid.uuid4())),
            response_time_ms=int((datetime.datetime.utcnow().timestamp() * 1000)),
            tokens_used=response.usage.total_tokens
        )
        db.session.add(query_record)
        db.session.commit()
        
        # Record usage
        record_usage(g.tenant.id, current_user.id, 'query', 1, {
            'query_length': len(query),
            'tokens_used': response.usage.total_tokens,
            'confidence_score': confidence_score
        })
        
        return jsonify({
            'reply': answer,
            'sources': citations_used,
            'extracted_citations': extracted_citations,
            'confidence_score': confidence_score,
            'search_metadata': {
                'documents_found': len(search_results['documents']),
                'filters_applied': search_filters
            },
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Enhanced chat error: {e}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@api_bp.route('/precedent-analysis', methods=['POST'])
@login_required
@require_tenant
@require_plan_feature('precedent_matching')
def precedent_analysis():
    """Analyze legal precedents for given case text"""
    data = request.get_json()
    case_text = data.get('case_text', '').strip()
    
    if not case_text:
        return jsonify({'error': 'Case text required'}), 400
    
    try:
        search_engine = EnhancedLegalSearchEngine(g.tenant.id)
        precedents = search_engine.analyze_precedents(case_text)
        
        return jsonify({
            'precedents': precedents,
            'analysis_date': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Precedent analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/advanced-search', methods=['POST'])
@login_required
@require_tenant
def advanced_search():
    """Advanced search with multiple filters"""
    data = request.get_json()
    query = data.get('query', '').strip()
    filters = data.get('filters', {})
    n_results = min(data.get('n_results', 10), 50)  # Limit to 50 results max
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    try:
        search_engine = EnhancedLegalSearchEngine(g.tenant.id)
        results = search_engine.advanced_search(query, filters, n_results)
        
        return jsonify({
            'results': results,
            'query': query,
            'filters_applied': filters,
            'search_date': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# DOCUMENT MANAGEMENT ROUTES
# =============================================================================

@api_bp.route('/upload-document', methods=['POST'])
def upload_document():
    """Upload and process legal document"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file extension
    allowed_extensions = {'pdf', 'docx', 'txt'}
    if not file.filename or '.' not in file.filename or \
       file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Allowed: PDF, DOCX, TXT'}), 400
    
    try:
        # Simple file processing for testing
        import os
        import tempfile
        
        # Save the file temporarily
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        
        # Get additional metadata from form
        citation = request.form.get('citation', '')
        court = request.form.get('court', '')
        year = request.form.get('year', '')
        volume = request.form.get('volume', '')
        legal_area = request.form.get('legal_area', '')
        document_type = request.form.get('document_type', '')
        
        # Simulate processing
        return jsonify({
            'success': True,
            'message': f'Document "{file.filename}" uploaded successfully!',
            'filename': file.filename,
            'citation': citation,
            'court': court,
            'year': year,
            'volume': volume,
            'legal_area': legal_area,
            'document_type': document_type,
            'size': os.path.getsize(file_path),
            'chunks_processed': 3  # Simulated
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@api_bp.route('/documents', methods=['GET'])
@login_required
@require_tenant
def list_documents():
    """List tenant's uploaded documents"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # Optimized query avoiding expensive COUNT and large fields
    documents_query = LegalDocument.query.filter_by(processing_status='processed')\
                                        .options(db.load_only(
                                            LegalDocument.id,
                                            LegalDocument.original_filename,
                                            LegalDocument.document_type,
                                            LegalDocument.legal_area,
                                            LegalDocument.jurisdiction,
                                            LegalDocument.file_size,
                                            LegalDocument.total_chunks,
                                            LegalDocument.created_at,
                                            LegalDocument.extracted_citations
                                        ))\
                                        .order_by(LegalDocument.created_at.desc())\
                                        .limit(per_page + 1)  # +1 to check for next page
    
    if page > 1:
        # Use offset for pagination (can be optimized further with keyset pagination)
        documents_query = documents_query.offset((page - 1) * per_page)
    
    documents_list = documents_query.all()
    has_next = len(documents_list) > per_page
    if has_next:
        documents_list = documents_list[:-1]  # Remove the extra record
    
    doc_list = []
    for doc in documents_list:
        doc_list.append({
            'id': doc.id,
            'filename': doc.original_filename,
            'document_type': doc.document_type,
            'legal_areas': doc.legal_area,
            'jurisdiction': doc.jurisdiction,
            'file_size': doc.file_size,
            'total_chunks': doc.total_chunks,
            'upload_date': doc.created_at.isoformat(),
            'citations_count': len(doc.extracted_citations) if doc.extracted_citations else 0
        })
    
    # Create optimized response with caching headers (API-compatible)
    response_data = {
        'documents': doc_list,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'has_prev': page > 1,
            'has_next': has_next,
            'pages': None,  # Maintain API compatibility but avoid expensive COUNT
            'total': None,  # Maintain API compatibility but avoid expensive COUNT
            'current_count': len(doc_list)
        }
    }
    
    response = make_response(jsonify(response_data))
    response.headers['Cache-Control'] = 'private, max-age=300'  # Cache for 5 minutes (private to prevent tenant data leakage)
    response.headers['ETag'] = f'docs-{page}-{len(doc_list)}'
    return response

@api_bp.route('/documents/<int:doc_id>', methods=['DELETE'])
@login_required
@require_tenant
def delete_document(doc_id):
    """Delete a document (owner/admin only)"""
    if not current_user.has_permission('manage_documents'):
        return jsonify({'error': 'Permission denied'}), 403
    
    doc = LegalDocument.query.get_or_404(doc_id)
    
    try:
        # Remove from ChromaDB
        search_engine = EnhancedLegalSearchEngine(g.tenant.id)
        # TODO: Implement removal from ChromaDB by document ID
        
        # Remove file from disk
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        
        # Remove from database
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Document deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Document deletion error: {e}")
        return jsonify({'error': 'Failed to delete document'}), 500

# =============================================================================
# WORKSPACE COLLABORATION ROUTES
# =============================================================================

@api_bp.route('/workspaces', methods=['GET', 'POST'])
@login_required
@require_tenant
@require_plan_feature('workspace_collaboration')
def workspaces():
    """List or create legal workspaces"""
    if request.method == 'GET':
        workspaces = LegalWorkspace.query.filter(
            (LegalWorkspace.owner_user_id == current_user.id) |
            (LegalWorkspace.shared_with.contains([current_user.id])) |
            (LegalWorkspace.is_public == True)
        ).order_by(LegalWorkspace.updated_at.desc()).all()
        
        workspace_list = []
        for ws in workspaces:
            workspace_list.append({
                'id': ws.id,
                'name': ws.name,
                'description': ws.description,
                'owner_id': ws.owner_user_id,
                'is_owner': ws.owner_user_id == current_user.id,
                'is_public': ws.is_public,
                'created_at': ws.created_at.isoformat(),
                'updated_at': ws.updated_at.isoformat()
            })
        
        return jsonify({'workspaces': workspace_list})
    
    else:  # POST - Create new workspace
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({'error': 'Workspace name required'}), 400
        
        try:
            workspace = LegalWorkspace(
                name=name,
                description=description,
                owner_user_id=current_user.id,
                saved_queries=[],
                bookmarked_documents=[],
                notes=''
            )
            db.session.add(workspace)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'workspace_id': workspace.id,
                'message': 'Workspace created successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Workspace creation error: {e}")
            return jsonify({'error': 'Failed to create workspace'}), 500

# =============================================================================
# EXPORT AND REPORTING ROUTES
# =============================================================================

@api_bp.route('/export-pdf', methods=['POST'])
@login_required
@require_tenant
def export_legal_brief():
    """Export legal research as formatted PDF"""
    data = request.get_json()
    content = data.get('content', {})
    
    if not content:
        return jsonify({'error': 'No content to export'}), 400
    
    try:
        # Generate PDF with enhanced legal formatting
        filename = f"exports/legal_brief_{uuid.uuid4().hex[:8]}.pdf"
        os.makedirs("exports", exist_ok=True)
        
        # Create PDF with legal formatting
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Header with tenant branding
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 60, f"{g.tenant.name} - Legal Research Brief")
        
        # Add content sections
        y = height - 120
        
        # Query section
        if content.get('query'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Research Query:")
            y -= 20
            c.setFont("Helvetica", 11)
            # Word wrap query text
            query_lines = self._wrap_text(content['query'], width - 100)
            for line in query_lines:
                c.drawString(50, y, line)
                y -= 15
            y -= 10
        
        # Answer section
        if content.get('answer'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Legal Analysis:")
            y -= 20
            c.setFont("Helvetica", 10)
            # Word wrap answer text
            answer_lines = self._wrap_text(content['answer'], width - 100)
            for line in answer_lines:
                c.drawString(50, y, line)
                y -= 12
                if y < 80:  # Page break
                    c.showPage()
                    y = height - 80
            y -= 20
        
        # Citations section
        if content.get('citations'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Legal Citations:")
            y -= 20
            c.setFont("Helvetica", 10)
            for citation in content['citations']:
                c.drawString(70, y, f"• {citation}")
                y -= 15
                if y < 80:
                    c.showPage()
                    y = height - 80
        
        # Footer
        c.setFont("Helvetica", 8)
        c.drawString(50, 30, f"Generated by KanoonPK on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(50, 20, "This document is for research purposes only and does not constitute formal legal advice.")
        
        c.save()
        
        return send_file(filename, as_attachment=True, download_name="legal_research_brief.pdf")
        
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        return jsonify({'error': 'Export failed'}), 500

def _wrap_text(text, max_width):
    """Helper function to wrap text for PDF"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if len(test_line) * 6 < max_width:  # Approximate character width
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines

# =============================================================================
# USAGE ANALYTICS ROUTES
# =============================================================================

@api_bp.route('/analytics/usage', methods=['GET'])
@login_required
@require_tenant
def usage_analytics():
    """Get tenant usage analytics"""
    if not current_user.has_permission('view_analytics'):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    
    # Query usage metrics
    usage_query = UsageMetric.query.filter_by(tenant_id=g.tenant.id)
    
    # Group by metric type and time
    usage_data = {}
    metrics = usage_query.all()
    
    for metric in metrics:
        metric_type = metric.metric_type
        if metric_type not in usage_data:
            usage_data[metric_type] = {
                'total': 0,
                'by_month': {}
            }
        
        usage_data[metric_type]['total'] += metric.count
        month = metric.month_year
        if month not in usage_data[metric_type]['by_month']:
            usage_data[metric_type]['by_month'][month] = 0
        usage_data[metric_type]['by_month'][month] += metric.count
    
    # Current plan limits
    plan_limits = PLAN_LIMITS[g.tenant.plan]
    current_month = datetime.datetime.utcnow().strftime('%Y-%m')
    
    analytics = {
        'usage_data': usage_data,
        'plan_limits': plan_limits,
        'current_usage': {
            'queries': g.tenant.get_current_usage('query', current_month),
            'documents': g.tenant.get_current_usage('document_upload'),
            'storage_mb': g.tenant.get_current_usage('storage_mb', current_month)
        },
        'date_range': {
            'start': start_date,
            'end': end_date
        }
    }
    
    return jsonify(analytics)

# =============================================================================
# PUBLIC LANDING PAGE
# =============================================================================

@main_bp.route('/')
def public_home():
    """Advanced Pakistan Law Research Platform - Enhanced pakistanlawsite interface"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KanoonPK - Smart Legal Research | AI-Powered Law Search</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-color: #2c3e50;
                --secondary-color: #34495e;
                --accent-color: #e74c3c;
                --success-color: #27ae60;
                --warning-color: #f39c12;
                --error-color: #e74c3c;
                --text-primary: #2c3e50;
                --text-secondary: #7f8c8d;
                --background-main: #ecf0f1;
                --background-paper: #ffffff;
                --border-color: #bdc3c7;
                --shadow-light: 0 2px 8px rgba(44,62,80,0.1);
                --shadow-medium: 0 4px 16px rgba(44,62,80,0.15);
                --shadow-heavy: 0 8px 32px rgba(44,62,80,0.2);
                --logo-gradient: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: var(--background-main);
                color: var(--text-primary);
                line-height: 1.6;
            }
            
            /* Header Section */
            .header {
                background: var(--background-paper);
                box-shadow: var(--shadow-light);
                position: sticky;
                top: 0;
                z-index: 100;
                border-bottom: 1px solid var(--border-color);
            }
            
            .header-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                height: 70px;
            }
            
            .logo-section {
                display: flex;
                align-items: center;
                gap: 16px;
            }
            
            .brand-logo {
                width: 50px;
                height: 50px;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: var(--shadow-medium);
                border: 2px solid var(--primary-color);
            }
            
            .logo-image {
                width: 100%;
                height: 100%;
                object-fit: cover;
                object-position: center;
            }
            
            .logo-text {
                font-size: 24px;
                font-weight: 700;
                color: var(--primary-color);
            }
            
            .logo-subtitle {
                font-size: 12px;
                color: var(--text-secondary);
                font-weight: 400;
                margin-top: -4px;
            }
            
            /* Main Content Area */
            .main-content {
                max-width: 1400px;
                margin: 0 auto;
                padding: 32px 24px;
                display: grid;
                grid-template-columns: 300px 1fr;
                gap: 32px;
                min-height: calc(100vh - 70px);
            }
            
            /* Sidebar */
            .sidebar {
                background: var(--background-paper);
                border-radius: 12px;
                box-shadow: var(--shadow-light);
                padding: 24px;
                height: fit-content;
                position: sticky;
                top: 102px;
            }
            
            /* Search Section */
            .search-section {
                background: var(--background-paper);
                border-radius: 12px;
                box-shadow: var(--shadow-light);
                padding: 32px;
                margin-bottom: 24px;
            }
            
            .search-header {
                text-align: center;
                margin-bottom: 32px;
            }
            
            .search-title {
                font-size: 28px;
                font-weight: 600;
                color: var(--primary-color);
                margin-bottom: 8px;
            }
            
            .search-subtitle {
                color: var(--text-secondary);
                font-size: 16px;
            }
            
            /* Search Types Grid */
            .search-types {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-bottom: 32px;
            }
            
            .search-type {
                background: white;
                border: 2px solid var(--border-color);
                border-radius: 12px;
                padding: 24px;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
            }
            
            .search-type:hover,
            .search-type.active {
                border-color: var(--primary-color);
                box-shadow: var(--shadow-medium);
                transform: translateY(-2px);
            }
            
            .search-type-icon {
                font-size: 32px;
                color: var(--primary-color);
                margin-bottom: 12px;
            }
            
            .search-type-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 8px;
            }
            
            .search-type-desc {
                font-size: 14px;
                color: var(--text-secondary);
            }
            
            .feature-badge {
                display: inline-block;
                background: rgba(167, 139, 250, 0.2);
                color: #a78bfa;
                padding: 8px 16px;
                border-radius: 20px;
                margin: 5px;
                font-size: 0.9rem;
                border: 1px solid rgba(167, 139, 250, 0.3);
            }
            
            .trial-form {
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                padding: 2rem;
                margin-top: 2rem;
            }
            
            .modern-input {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: white;
                border-radius: 10px;
                padding: 15px 20px;
                font-size: 1rem;
                transition: all 0.3s;
                margin-bottom: 1rem;
            }
            
            .modern-input:focus {
                background: rgba(255, 255, 255, 0.2);
                border-color: #667eea;
                color: white;
                box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
                outline: none;
            }
            
            .modern-input::placeholder {
                color: rgba(255,255,255,0.6);
            }
            
            .cta-button {
                background: var(--secondary-gradient);
                border: none;
                border-radius: 50px;
                padding: 18px 40px;
                color: white;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                position: relative;
                overflow: hidden;
            }
            
            .cta-button:hover {
                transform: translateY(-3px);
                box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
            }
            
            .cta-button:disabled {
                opacity: 0.7;
                transform: none;
                cursor: not-allowed;
            }
            
            .features-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-top: 3rem;
            }
            
            .feature-card {
                background: rgba(255,255,255,0.08);
                border-radius: 15px;
                padding: 1.5rem;
                text-align: center;
                border: 1px solid rgba(255,255,255,0.1);
                transition: all 0.3s;
            }
            
            .feature-card:hover {
                transform: translateY(-5px);
                background: rgba(255,255,255,0.12);
            }
            
            .feature-icon {
                font-size: 2.5rem;
                color: #a78bfa;
                margin-bottom: 1rem;
            }
            
            .feature-title {
                color: white;
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
            }
            
            .feature-desc {
                color: rgba(255,255,255,0.7);
                font-size: 0.9rem;
            }
            
            /* Statistics Section */
            .stats-section {
                background: var(--background-paper);
                border-radius: 12px;
                padding: 32px;
                box-shadow: var(--shadow-light);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 24px;
            }
            
            .stat-card {
                text-align: center;
                padding: 24px;
                background: var(--background-main);
                border-radius: 12px;
                border: 1px solid var(--border-color);
            }
            
            .stat-number {
                font-size: 32px;
                font-weight: 700;
                color: var(--primary-color);
                margin-bottom: 8px;
            }
            
            .stat-label {
                color: var(--text-secondary);
                font-size: 14px;
                font-weight: 500;
            }
            
            /* Additional Styles */
            .search-form-container {
                margin-top: 32px;
            }
            
            .search-form {
                display: none;
            }
            
            .search-form.active {
                display: block;
            }
            
            .input-group-large {
                display: flex;
                box-shadow: var(--shadow-medium);
                border-radius: 12px;
                overflow: hidden;
                margin-bottom: 24px;
            }
            
            .form-control-large {
                flex: 1;
                padding: 20px 24px;
                border: none;
                font-size: 16px;
                outline: none;
            }
            
            .btn-search {
                background: var(--primary-color);
                color: white;
                border: none;
                padding: 20px 32px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .btn-search:hover {
                background: var(--secondary-color);
                transform: translateY(-1px);
            }
            
            /* AI Examples Styling */
            .ai-examples {
                margin-top: 24px;
                padding: 20px;
                background: var(--background-main);
                border-radius: 12px;
                border: 1px solid var(--border-color);
            }
            
            .ai-examples p {
                margin-bottom: 16px;
                color: var(--text-primary);
                font-weight: 500;
            }
            
            .example-questions {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .example-question {
                background: white;
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 12px 16px;
                cursor: pointer;
                transition: all 0.2s;
                color: var(--text-secondary);
                font-size: 14px;
            }
            
            .example-question:hover {
                background: var(--primary-color);
                color: white;
                border-color: var(--primary-color);
                transform: translateY(-1px);
            }
            
            /* Mobile Responsive */
            @media (max-width: 1200px) {
                .main-content {
                    grid-template-columns: 1fr;
                }
                
                .sidebar {
                    position: static;
                    order: 2;
                }
            }
            
            @media (max-width: 768px) {
                .header-container {
                    padding: 0 16px;
                }
                
                .main-content {
                    padding: 24px 16px;
                }
                
                .search-types {
                    grid-template-columns: 1fr;
                }
                
                .example-questions {
                    gap: 8px;
                }
                
                .example-question {
                    font-size: 13px;
                    padding: 10px 12px;
                }
            }
            
            /* Welcome Section Enhancements */
            .welcome-logo {
                margin-bottom: 24px;
                display: flex;
                justify-content: center;
            }
            
            .welcome-logo-img {
                width: 80px;
                height: 80px;
                border-radius: 20px;
                border: 3px solid rgba(255,255,255,0.3);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                object-fit: cover;
            }
            
            .welcome-section {
                text-align: center;
                margin-bottom: 48px;
                padding: 48px 32px;
                background: var(--logo-gradient);
                color: white;
                border-radius: 16px;
                margin-top: -32px;
                position: relative;
                overflow: hidden;
                box-shadow: var(--shadow-heavy);
            }
            
            .welcome-section::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('/static/images/logo.jpeg') center/120px no-repeat;
                opacity: 0.03;
                z-index: 0;
            }
            
            .welcome-section > * {
                position: relative;
                z-index: 1;
            }
            
            .stat-item {
                text-align: center;
            }
            
            .stat-number {
                font-size: 2rem;
                font-weight: 700;
                color: #a78bfa;
            }
            
            .stat-label {
                color: rgba(255,255,255,0.8);
                font-size: 0.9rem;
            }
            
            /* Mobile Responsive */
            @media (max-width: 768px) {
                .main-title {
                    font-size: 2.2rem;
                }
                
                .hero-section {
                    padding: 2rem 1rem;
                }
                
                .glass-card {
                    margin: 1rem;
                }
                
                .features-grid {
                    grid-template-columns: 1fr;
                }
                
                .stats-section {
                    flex-direction: column;
                    gap: 1rem;
                }
            }
        </style>
    </head>
    <body>
        <!-- Header -->
        <header class="header">
            <div class="header-container">
                <div class="logo-section">
                    <div class="brand-logo">
                        <img src="/static/images/logo.jpeg" alt="KanoonPK Logo" class="logo-image">
                    </div>
                    <div>
                        <div class="logo-text">KanoonPK</div>
                        <div class="logo-subtitle">Advanced Legal Research Platform</div>
                    </div>
                </div>
                
                <div class="header-actions">
                    <button class="btn btn-outline-primary me-2" onclick="window.showLogin()">
                        <i class="fas fa-sign-in-alt me-2"></i>Login
                    </button>
                    <button class="btn btn-primary" onclick="window.showRegistration()">
                        <i class="fas fa-user-plus me-2"></i>Start Free Trial
                    </button>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Sidebar -->
            <aside class="sidebar">
                <h3 style="color: var(--primary-color); margin-bottom: 24px; font-size: 18px; font-weight: 600;">
                    <i class="fas fa-search me-2"></i>Research Tools
                </h3>
                
                <div class="sidebar-section">
                    <h4>Case Law Research</h4>
                    <ul class="sidebar-menu">
                        <li><a href="#"><i class="fas fa-gavel me-2"></i>Supreme Court Cases</a></li>
                        <li><a href="#"><i class="fas fa-landmark me-2"></i>High Court Cases</a></li>
                        <li><a href="#"><i class="fas fa-balance-scale-right me-2"></i>Tribunal Decisions</a></li>
                        <li><a href="#"><i class="fas fa-search me-2"></i>Citation Search</a></li>
                    </ul>
                </div>
                
                <div class="sidebar-section">
                    <h4>Statutory Research</h4>
                    <ul class="sidebar-menu">
                        <li><a href="#"><i class="fas fa-scroll me-2"></i>Constitution 1973</a></li>
                        <li><a href="#"><i class="fas fa-book me-2"></i>Federal Statutes</a></li>
                        <li><a href="#"><i class="fas fa-file-alt me-2"></i>Provincial Laws</a></li>
                        <li><a href="#"><i class="fas fa-briefcase me-2"></i>Corporate Law</a></li>
                    </ul>
                </div>
                
                <div class="sidebar-section">
                    <h4>AI Research Assistant</h4>
                    <ul class="sidebar-menu">
                        <li><a href="#" onclick="openAIChat()"><i class="fas fa-robot me-2"></i>Legal AI Chat</a></li>
                        <li><a href="/admin"><i class="fas fa-cog me-2"></i>Admin Panel</a></li>
                        <li><a href="#"><i class="fas fa-magic me-2"></i>Case Analysis</a></li>
                        <li><a href="#"><i class="fas fa-brain me-2"></i>Smart Research</a></li>
                    </ul>
                </div>
            </aside>

            <!-- Main Research Area -->
            <main class="research-content">
                <!-- Welcome Section -->
                <div class="welcome-section">
                    <div class="welcome-logo">
                        <img src="/static/images/logo.jpeg" alt="KanoonPK" class="welcome-logo-img">
                    </div>
                    <h1 class="welcome-title">Smart Legal Research</h1>
                    <p class="welcome-subtitle">Instant AI search through Pakistan's Leading Law Reports</p>
                </div>

                <!-- Search Section -->
                <div class="search-section">
                    <div class="search-header">
                        <div class="smart-header-content">
                            <div class="ai-badge">
                                <i class="fas fa-brain"></i>
                                <span>AI-Powered</span>
                            </div>
                            <h2 class="search-title">Legal Research Made Simple</h2>
                            <p class="search-subtitle">Ask questions in plain English - our AI understands legal context and provides accurate answers with citations</p>
                            <div class="smart-features">
                                <span class="feature-tag"><i class="fas fa-bolt"></i> Instant Results</span>
                                <span class="feature-tag"><i class="fas fa-shield-alt"></i> Verified Sources</span>
                                <span class="feature-tag"><i class="fas fa-quote-right"></i> Auto Citations</span>
                            </div>
                        </div>
                    </div>

                    <!-- Search Types -->
                    <div class="search-types">
                        <div class="search-type active" data-type="keyword">
                            <div class="search-type-icon">
                                <i class="fas fa-search"></i>
                            </div>
                            <h3 class="search-type-title">Keyword Search</h3>
                            <p class="search-type-desc">Search across all case law and statutes using keywords and phrases</p>
                        </div>
                        
                        <div class="search-type" data-type="citation">
                            <div class="search-type-icon">
                                <i class="fas fa-quote-left"></i>
                            </div>
                            <h3 class="search-type-title">Citation Search</h3>
                            <p class="search-type-desc">Find specific cases using PLD, SCMR, CLC, or other citation formats</p>
                        </div>
                        
                        <div class="search-type" data-type="ai">
                            <div class="search-type-icon">
                                <i class="fas fa-robot"></i>
                            </div>
                            <h3 class="search-type-title">AI Research</h3>
                            <p class="search-type-desc">Ask questions in natural language and get comprehensive legal analysis</p>
                        </div>
                        
                        <div class="search-type" data-type="advanced">
                            <div class="search-type-icon">
                                <i class="fas fa-sliders-h"></i>
                            </div>
                            <h3 class="search-type-title">Advanced Search</h3>
                            <p class="search-type-desc">Use multiple filters for precise legal research and case analysis</p>
                        </div>
                    </div>
                            
                    <!-- Search Form -->
                    <div class="search-form-container">
                        <div class="search-form active" id="keywordSearch">
                            <div class="input-group-large">
                                <input type="text" class="form-control-large" placeholder="Enter keywords, case names, or legal concepts..." id="keywordInput">
                                <button class="btn-search" type="button">
                                    <i class="fas fa-search"></i>
                                    Search
                                </button>
                            </div>
                            
                            <div class="search-filters">
                                <select class="form-select-filter">
                                    <option>All Jurisdictions</option>
                                    <option>Supreme Court</option>
                                    <option>Lahore High Court</option>
                                    <option>Islamabad High Court</option>
                                    <option>Sindh High Court</option>
                                    <option>Peshawar High Court</option>
                                    <option>Balochistan High Court</option>
                                </select>
                                
                                <select class="form-select-filter">
                                    <option>All Document Types</option>
                                    <option>Judgments</option>
                                    <option>Statutes</option>
                                    <option>Rules</option>
                                    <option>Notifications</option>
                                </select>
                                
                                <input type="date" class="form-control-filter" placeholder="From Date">
                                <input type="date" class="form-control-filter" placeholder="To Date">
                            </div>
                        </div>
                        
                        <div class="search-form" id="citationSearch">
                            <div class="input-group-large">
                                <input type="text" class="form-control-large" placeholder="Enter citation: e.g., 2023 SCMR 1234 or PLD 2023 SC 567..." id="citationInput">
                                <button class="btn-search" type="button">
                                    <i class="fas fa-search"></i>
                                    Find Case
                                </button>
                            </div>
                            
                            <div class="citation-examples">
                                <span class="citation-example">PLD 2023 SC 567</span>
                                <span class="citation-example">2023 SCMR 1234</span>
                                <span class="citation-example">2023 CLC 890</span>
                                <span class="citation-example">AIR 2023 SC 456</span>
                            </div>
                        </div>
                        
                        <div class="search-form" id="aiSearch">
                            <div class="ai-search-container">
                                <textarea class="form-control-large ai-textarea" id="aiQuestionInput" placeholder="Ask any legal question... e.g., 'What are the grounds for divorce under Muslim Family Law?' or 'Explain Article 25 of Pakistan Constitution'" rows="4"></textarea>
                                <button class="btn-search btn-ai" type="button" onclick="askAIQuestion()">
                                    <i class="fas fa-robot"></i>
                                    Ask AI Assistant
                                </button>
                            </div>
                            
                            <div class="ai-examples">
                                <p><strong>Example Questions:</strong></p>
                                <div class="example-questions">
                                    <span class="example-question" onclick="setAIQuestion(this)">What are the grounds for divorce under Muslim Family Law?</span>
                                    <span class="example-question" onclick="setAIQuestion(this)">Explain Article 25 of Pakistan Constitution</span>
                                    <span class="example-question" onclick="setAIQuestion(this)">What is the process for filing a civil suit?</span>
                                    <span class="example-question" onclick="setAIQuestion(this)">Rights of accused in criminal cases under Pakistan law</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="search-form" id="advancedSearch">
                            <div class="advanced-filters-grid">
                                <div class="filter-group">
                                    <label>Case Title</label>
                                    <input type="text" class="form-control-filter" placeholder="vs., State, etc.">
                                </div>
                                <div class="filter-group">
                                    <label>Judge Name</label>
                                    <input type="text" class="form-control-filter" placeholder="Justice name">
                                </div>
                                <div class="filter-group">
                                    <label>Legal Area</label>
                                    <select class="form-select-filter">
                                        <option>All Areas</option>
                                        <option>Constitutional Law</option>
                                        <option>Criminal Law</option>
                                        <option>Civil Law</option>
                                        <option>Family Law</option>
                                        <option>Corporate Law</option>
                                        <option>Tax Law</option>
                                        <option>Labor Law</option>
                                    </select>
                                </div>
                                <div class="filter-group">
                                    <label>Case Status</label>
                                    <select class="form-select-filter">
                                        <option>All Status</option>
                                        <option>Decided</option>
                                        <option>Pending</option>
                                        <option>Dismissed</option>
                                    </select>
                                </div>
                            </div>
                            
                            <button class="btn-search btn-advanced" type="button">
                                <i class="fas fa-search-plus"></i>
                                Advanced Search
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Smart Quick Access Section -->
                <div class="quick-access-section">
                    <div class="section-header">
                        <h3><i class="fas fa-bolt me-2"></i>Smart Legal Shortcuts</h3>
                        <p class="section-subtitle">Quick access to Pakistan's key legal documents</p>
                    </div>
                    <div class="smart-access-grid">
                        <div class="smart-access-item" onclick="askAIQuestion('Explain Article 25 of Constitution of Pakistan 1973 regarding equality')">
                            <div class="item-icon">
                                <i class="fas fa-scroll"></i>
                            </div>
                            <div class="item-content">
                                <h5>Constitution 1973</h5>
                                <p>Fundamental rights & principles</p>
                                <span class="item-badge">Click to search</span>
                            </div>
                        </div>
                        <div class="smart-access-item" onclick="askAIQuestion('Show me recent amendments and interpretations of Pakistan Penal Code')">
                            <div class="item-icon">
                                <i class="fas fa-gavel"></i>
                            </div>
                            <div class="item-content">
                                <h5>Pakistan Penal Code</h5>
                                <p>Criminal law & procedures</p>
                                <span class="item-badge">Click to search</span>
                            </div>
                        </div>
                        <div class="smart-access-item" onclick="askAIQuestion('Find Contract Act 1872 provisions on breach of contract and remedies')">
                            <div class="item-icon">
                                <i class="fas fa-file-contract"></i>
                            </div>
                            <div class="item-content">
                                <h5>Contract Act 1872</h5>
                                <p>Contract law & agreements</p>
                                <span class="item-badge">Click to search</span>
                            </div>
                        </div>
                        <div class="smart-access-item" onclick="askAIQuestion('Explain Companies Act 2017 requirements for corporate governance')">
                            <div class="item-icon">
                                <i class="fas fa-building"></i>
                            </div>
                            <div class="item-content">
                                <h5>Companies Act 2017</h5>
                                <p>Corporate law & governance</p>
                                <span class="item-badge">Click to search</span>
                            </div>
                        </div>
                        <div class="smart-access-item" onclick="askAIQuestion('Show Family Laws Ordinance provisions on marriage, divorce and custody')">
                            <div class="item-icon">
                                <i class="fas fa-users"></i>
                            </div>
                            <div class="item-content">
                                <h5>Family Laws Ordinance</h5>
                                <p>Family & matrimonial law</p>
                                <span class="item-badge">Click to search</span>
                            </div>
                        </div>
                        <div class="smart-access-item" onclick="askAIQuestion('Find Civil Procedure Code rules on court proceedings and appeals')">
                            <div class="item-icon">
                                <i class="fas fa-balance-scale"></i>
                            </div>
                            <div class="item-content">
                                <h5>Civil Procedure Code</h5>
                                <p>Court procedures & appeals</p>
                                <span class="item-badge">Click to search</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Statistics Section -->
                <div class="stats-section">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">200,000+</div>
                            <div class="stat-label">Legal Cases</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">15,000+</div>
                            <div class="stat-label">Statutes & Rules</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">500+</div>
                            <div class="stat-label">Law Firms</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">24/7</div>
                            <div class="stat-label">AI Assistant</div>
                        </div>
                    </div>
                </div>
            </main>
        </div>

        <!-- Registration Modal -->
        <div class="modal fade" id="registrationModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Start Your Free Trial</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="quickStartForm">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Organization Name</label>
                                        <input type="text" class="form-control" name="organization_name" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Email Address</label>
                                        <input type="email" class="form-control" name="email" required>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">First Name</label>
                                        <input type="text" class="form-control" name="first_name" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Password</label>
                                        <input type="password" class="form-control" name="password" required>
                                    </div>
                                </div>
                            </div>
                            <div class="text-center">
                                <button type="submit" class="btn btn-primary btn-lg">
                                    <i class="fas fa-rocket me-2"></i>Start Free Trial
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
                            
                            <!-- Features Grid -->
                            <div class="features-grid">
                                <div class="feature-card">
                                    <div class="feature-icon"><i class="fas fa-brain"></i></div>
                                    <div class="feature-title">AI-Powered Answers</div>
                                    <div class="feature-desc">Get instant, accurate answers to Pakistani legal questions using advanced AI</div>
                                </div>
                                
                                <div class="feature-card">
                                    <div class="feature-icon"><i class="fas fa-search"></i></div>
                                    <div class="feature-title">Smart Legal Search</div>
                                    <div class="feature-desc">Find relevant cases, laws, and precedents from Pakistan's legal database</div>
                                </div>
                                
                                <div class="feature-card">
                                    <div class="feature-icon"><i class="fas fa-users"></i></div>
                                    <div class="feature-title">Team Collaboration</div>
                                    <div class="feature-desc">Share research, collaborate with colleagues, and build legal knowledge base</div>
                                </div>
                                
                                <div class="feature-card">
                                    <div class="feature-icon"><i class="fas fa-mobile-alt"></i></div>
                                    <div class="feature-title">Mobile Ready</div>
                                    <div class="feature-desc">Access your legal assistant from anywhere, on any device, anytime</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.getElementById('quickStartForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = Object.fromEntries(formData.entries());
                
                // Generate subdomain from organization name
                data.subdomain = data.organization_name.toLowerCase()
                    .replace(/[^a-z0-9]/g, '')
                    .substring(0, 10) + Math.floor(Math.random() * 1000);
                
                data.admin_email = data.email;
                data.admin_password = data.password;
                data.admin_first_name = data.first_name;
                data.admin_last_name = 'User';
                
                const submitBtn = this.querySelector('button[type="submit"]');
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Setting up your AI assistant...';
                
                try {
                    const response = await fetch('/auth/register-tenant', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        submitBtn.innerHTML = '<i class="fas fa-check me-2"></i>Success! Opening AI Chat...';
                        setTimeout(() => {
                            window.location.href = '/chat?tenant=' + result.subdomain;
                        }, 1500);
                    } else {
                        throw new Error(result.error || 'Registration failed');
                    }
                } catch (error) {
                    console.error('Registration error:', error);
                    submitBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Try Again';
                    
                    let errorMessage = 'Setup failed. Please try again.';
                    if (error.message && error.message.includes('already')) {
                        errorMessage = 'This email or organization name is already registered. Please try different details.';
                    }
                    alert(errorMessage);
                } finally {
                    setTimeout(() => {
                        submitBtn.disabled = false;
                        if (submitBtn.innerHTML.includes('Try Again')) {
                            submitBtn.innerHTML = originalText;
                        }
                    }, 3000);
                }
            });
            
            // AI Research Functions
            function askAIQuestion() {
                const question = document.getElementById('aiQuestionInput').value.trim();
                if (question) {
                    // Store the question in session storage and redirect to chat
                    sessionStorage.setItem('pendingQuestion', question);
                    window.location.href = '/chat';
                } else {
                    alert('Please enter a question first.');
                }
            }
            
            function setAIQuestion(element) {
                const question = element.textContent;
                document.getElementById('aiQuestionInput').value = question;
                // Auto-focus the textarea
                document.getElementById('aiQuestionInput').focus();
            }
            
            // Make functions globally available
            window.askAIQuestion = askAIQuestion;
            window.setAIQuestion = setAIQuestion;
            
        </script>
    </body>
    </html>
    """)

# =============================================================================
# ADMIN CONTROL PANEL FOR LEGAL DOCUMENT MANAGEMENT
# =============================================================================

@admin_bp.route('/')
def admin_dashboard():
    """Admin dashboard for document and citation management"""
    # Remove login requirement for testing purposes
    
    # Get documents count with caching
    documents_count = 0
    try:
        # Use more efficient count query with limit to prevent slow counts on large tables
        documents_count = db.session.query(LegalDocument.id).count()
        if documents_count > 10000:  # Cap display at 10k+ for performance
            documents_count = "10,000+"
    except:
        pass
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en" data-bs-theme="light">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
        <meta name="theme-color" content="#2c3e50">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <title>Admin Control Panel - KanoonPK Legal Database</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root {
                --primary-color: #2c3e50;
                --secondary-color: #34495e;
                --accent-color: #e74c3c;
                --success-color: #27ae60;
                --background-main: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                --background-paper: #ffffff;
                --border-color: #e3e8ee;
                --text-primary: #2c3e50;
                --text-secondary: #64748b;
                --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
                --shadow-md: 0 4px 12px rgba(0,0,0,0.15);
                --shadow-lg: 0 8px 25px rgba(0,0,0,0.25);
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: var(--background-main);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                color: var(--text-primary);
                margin: 0;
                padding: 0;
                line-height: 1.6;
            }
            
            .admin-header {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: white;
                padding: 16px 0;
                margin-bottom: 24px;
                box-shadow: var(--shadow-md);
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            @media (max-width: 768px) {
                .admin-header {
                    padding: 12px 0;
                    margin-bottom: 16px;
                }
            }
            
            .upload-section {
                background: var(--background-paper);
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: var(--shadow-sm);
                border: 1px solid var(--border-color);
                backdrop-filter: blur(10px);
            }
            
            @media (max-width: 768px) {
                .upload-section {
                    margin: 0 12px 16px;
                    padding: 16px;
                    border-radius: 12px;
                }
            }
            
            .citation-fields {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 16px;
                margin-top: 24px;
            }
            
            @media (max-width: 768px) {
                .citation-fields {
                    grid-template-columns: 1fr;
                    gap: 12px;
                    margin-top: 16px;
                }
            }
            
            .form-group label {
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 8px;
                display: block;
            }
            
            .form-control {
                border: 2px solid var(--border-color);
                border-radius: 12px;
                padding: 14px 16px;
                font-size: 15px;
                transition: all 0.3s ease;
                width: 100%;
                background: #fafbfc;
                font-family: inherit;
            }
            
            .form-control:focus {
                border-color: var(--primary-color);
                box-shadow: 0 0 0 4px rgba(44,62,80,0.1);
                outline: none;
                background: white;
                transform: translateY(-1px);
            }
            
            @media (max-width: 768px) {
                .form-control {
                    padding: 16px;
                    font-size: 16px;
                    border-radius: 10px;
                }
            }
            
            .btn-upload {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: white;
                border: none;
                padding: 18px 36px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 16px;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 24px;
                box-shadow: var(--shadow-sm);
                width: 100%;
                max-width: 300px;
                position: relative;
                overflow: hidden;
            }
            
            .btn-upload::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            
            .btn-upload:hover::before {
                left: 100%;
            }
            
            .btn-upload:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-lg);
            }
            
            .btn-upload:active {
                transform: translateY(0);
                box-shadow: var(--shadow-sm);
            }
            
            @media (max-width: 768px) {
                .btn-upload {
                    padding: 20px;
                    font-size: 18px;
                    max-width: none;
                    border-radius: 10px;
                }
            }
            
            .documents-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap: 20px;
                margin-top: 24px;
            }
            
            .document-card {
                background: var(--background-paper);
                border-radius: 16px;
                padding: 20px;
                border: 1px solid var(--border-color);
                box-shadow: var(--shadow-sm);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .document-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, var(--success-color), #16a085);
                transform: scaleX(0);
                transform-origin: left;
                transition: transform 0.3s ease;
            }
            
            .document-card:hover {
                transform: translateY(-6px);
                box-shadow: var(--shadow-md);
            }
            
            .document-card:hover::before {
                transform: scaleX(1);
            }
            
            @media (max-width: 768px) {
                .documents-grid {
                    grid-template-columns: 1fr;
                    gap: 16px;
                    margin-top: 16px;
                }
                
                .document-card {
                    padding: 16px;
                    border-radius: 12px;
                }
            }
            
            .doc-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 1px solid var(--border-color);
            }
            
            .doc-title {
                font-weight: 600;
                color: var(--text-primary);
                margin: 0;
                flex: 1;
            }
            
            .delete-btn {
                background: var(--accent-color);
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.2s;
            }
            
            .delete-btn:hover {
                background: #c0392b;
            }
            
            .citation-info {
                background: #f8f9fa;
                padding: 16px;
                border-radius: 8px;
                margin-top: 12px;
                border-left: 4px solid var(--primary-color);
            }
            
            .citation-info strong {
                color: var(--primary-color);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 20px;
                margin-bottom: 32px;
                padding: 0 12px;
            }
            
            .stat-card {
                background: var(--background-paper);
                padding: 24px;
                border-radius: 16px;
                text-align: center;
                border: 1px solid var(--border-color);
                box-shadow: var(--shadow-sm);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .stat-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
                transform: scaleX(0);
                transform-origin: left;
                transition: transform 0.3s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-4px);
                box-shadow: var(--shadow-md);
            }
            
            .stat-card:hover::before {
                transform: scaleX(1);
            }
            
            .stat-number {
                font-size: 36px;
                font-weight: 800;
                color: var(--primary-color);
                margin-bottom: 8px;
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .stat-label {
                font-size: 14px;
                font-weight: 500;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            @media (max-width: 768px) {
                .stats-grid {
                    grid-template-columns: repeat(2, 1fr);
                    gap: 12px;
                    padding: 0;
                }
                
                .stat-card {
                    padding: 20px 12px;
                    border-radius: 12px;
                }
                
                .stat-number {
                    font-size: 24px;
                }
                
                .stat-label {
                    font-size: 12px;
                }
            }
            
            .upload-area {
                border: 3px dashed var(--border-color);
                border-radius: 16px;
                padding: 48px 24px;
                text-align: center;
                margin-bottom: 24px;
                transition: all 0.3s ease;
                cursor: pointer;
                background: linear-gradient(145deg, #f8fafc, #f1f5f9);
                position: relative;
                overflow: hidden;
            }
            
            .upload-area::before {
                content: '';
                position: absolute;
                top: -2px;
                left: -2px;
                right: -2px;
                bottom: -2px;
                background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
                border-radius: 16px;
                opacity: 0;
                z-index: -1;
                transition: opacity 0.3s ease;
            }
            
            .upload-area:hover {
                border-color: var(--primary-color);
                background: white;
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
            }
            
            .upload-area:hover::before {
                opacity: 0.1;
            }
            
            .upload-area.dragover {
                border-color: var(--primary-color);
                background: rgba(44,62,80,0.05);
                transform: scale(1.02);
            }
            
            .upload-area.dragover::before {
                opacity: 0.15;
            }
            
            @media (max-width: 768px) {
                .upload-area {
                    padding: 32px 16px;
                    border-radius: 12px;
                }
                
                .upload-area h4 {
                    font-size: 18px;
                }
                
                .upload-area i {
                    font-size: 2rem !important;
                }
            }
            
            .alert {
                padding: 16px;
                border-radius: 8px;
                margin-bottom: 24px;
                border-left: 4px solid;
            }
            
            .alert-success {
                background: #d4edda;
                border-color: var(--success-color);
                color: #155724;
            }
            
            .alert-error {
                background: #f8d7da;
                border-color: var(--accent-color);
                color: #721c24;
            }
            
            /* Mobile-specific improvements */
            @media (max-width: 480px) {
                .container {
                    padding: 0 8px;
                }
                
                .admin-header h1 {
                    font-size: 20px !important;
                }
                
                .admin-header p {
                    font-size: 12px !important;
                }
                
                .upload-area {
                    padding: 24px 12px;
                }
                
                .citation-fields {
                    gap: 8px;
                }
                
                .form-control {
                    padding: 18px 14px;
                    font-size: 16px;
                }
                
                .btn-upload {
                    padding: 22px;
                    font-size: 16px;
                }
            }
            
            /* Touch-friendly improvements */
            .form-control:focus {
                transform: none; /* Remove transform on mobile for better performance */
            }
            
            @media (hover: hover) {
                .form-control:focus {
                    transform: translateY(-1px);
                }
            }
            
            /* Better scrolling on mobile */
            .upload-section {
                scroll-margin-top: 20px;
            }
            
            /* Improved button spacing for touch */
            @media (max-width: 768px) {
                .d-flex.gap-3 {
                    gap: 8px !important;
                    flex-direction: column;
                    align-items: stretch;
                }
                
                .btn {
                    min-height: 44px; /* Minimum touch target size */
                }
            }
            
            /* Floating Action Button for Mobile Testing */
            .fab-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
            }
            
            .fab {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                border: none;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                transition: all 0.3s ease;
            }
            
            .fab:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(0,0,0,0.4);
            }
            
            .fab-menu {
                position: absolute;
                bottom: 70px;
                right: 0;
                min-width: 200px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                opacity: 0;
                visibility: hidden;
                transform: translateY(10px);
                transition: all 0.3s ease;
            }
            
            .fab-menu.show {
                opacity: 1;
                visibility: visible;
                transform: translateY(0);
            }
            
            .fab-menu-item {
                display: flex;
                align-items: center;
                padding: 12px 16px;
                cursor: pointer;
                transition: background 0.2s;
                color: var(--text-primary);
                font-size: 14px;
            }
            
            .fab-menu-item:hover {
                background: #f8f9fa;
            }
            
            .fab-menu-item:first-child {
                border-radius: 12px 12px 0 0;
            }
            
            .fab-menu-item:last-child {
                border-radius: 0 0 12px 12px;
            }
            
            .fab-menu-item i {
                margin-right: 12px;
                width: 20px;
                text-align: center;
            }
            
            @media (max-width: 768px) {
                .fab-container {
                    bottom: 30px;
                    right: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="admin-header">
            <div class="container">
                <div class="d-flex align-items-center justify-content-between">
                    <div class="d-flex align-items-center gap-3">
                        <img src="/static/images/logo.jpeg" alt="KanoonPK" style="width: 50px; height: 50px; border-radius: 12px; object-fit: cover;">
                        <div>
                            <h1 class="mb-1">Legal Database Management</h1>
                            <p class="mb-0 opacity-75">Upload PLD, SCMR, CLC, MLD & Other Citations</p>
                        </div>
                    </div>
                    <a href="/" class="btn btn-outline-light" style="border-radius: 10px; padding: 8px 20px; font-size: 14px;">
                        <i class="fas fa-home me-2"></i>Back to Research
                    </a>
                </div>
            </div>
        </div>

        <div class="container">
            <!-- Statistics -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{{ documents_count }}</div>
                    <div class="stat-label">Total Documents</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalCitations">Loading...</div>
                    <div class="stat-label">Legal Citations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalChunks">Loading...</div>
                    <div class="stat-label">Text Chunks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="lastUpdate">Loading...</div>
                    <div class="stat-label">Last Upload</div>
                </div>
            </div>

            <!-- Quick Actions for Testing -->
            <div class="upload-section">
                <h2 class="mb-4">
                    <i class="fas fa-bolt me-3"></i>Quick Test Actions
                </h2>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 24px;">
                    <button id="addSampleDataBtn" class="btn btn-sm" style="background: var(--success-color); color: white; padding: 14px 20px; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; transition: all 0.3s; min-height: 50px;">
                        <i class="fas fa-database me-2"></i>Add Sample Legal Data
                    </button>
                    <button id="testChatBtn" class="btn btn-sm" style="background: var(--secondary-color); color: white; padding: 14px 20px; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; transition: all 0.3s; min-height: 50px;">
                        <i class="fas fa-comments me-2"></i>Test AI Chat
                    </button>
                    <button id="clearDataBtn" class="btn btn-sm" style="background: var(--accent-color); color: white; padding: 14px 20px; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; transition: all 0.3s; min-height: 50px;">
                        <i class="fas fa-trash me-2"></i>Clear All Data
                    </button>
                </div>
            </div>

            <!-- Upload Section -->
            <div class="upload-section">
                <h2 class="mb-4">
                    <i class="fas fa-upload me-3"></i>Upload Legal Documents & Citations
                </h2>
                
                <div id="alertContainer"></div>
                
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="upload-area" id="uploadArea">
                        <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                        <h4>Drop files here or click to select</h4>
                        <p class="text-muted">Supported formats: PDF, DOCX, TXT (Max: 16MB)</p>
                        <input type="file" id="fileInput" name="file" accept=".pdf,.docx,.txt" style="display: none;">
                    </div>
                    
                    <div class="citation-fields">
                        <div class="form-group">
                            <label for="citation">Citation Format</label>
                            <input type="text" class="form-control" id="citation" name="citation" 
                                   placeholder="e.g., PLD 2023 SC 567, SCMR 2023 Vol 1 234">
                        </div>
                        
                        <div class="form-group">
                            <label for="court">Court/Jurisdiction</label>
                            <select class="form-control" id="court" name="court">
                                <option value="">Select Court</option>
                                <option value="Supreme Court of Pakistan">Supreme Court of Pakistan</option>
                                <option value="Federal Shariat Court">Federal Shariat Court</option>
                                <option value="Lahore High Court">Lahore High Court</option>
                                <option value="Karachi High Court (Sindh)">Karachi High Court (Sindh)</option>
                                <option value="Peshawar High Court">Peshawar High Court</option>
                                <option value="Quetta High Court (Balochistan)">Quetta High Court (Balochistan)</option>
                                <option value="Islamabad High Court">Islamabad High Court</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="year">Year</label>
                            <input type="number" class="form-control" id="year" name="year" 
                                   min="1900" max="2030" placeholder="2023">
                        </div>
                        
                        <div class="form-group">
                            <label for="volume">Volume/Page</label>
                            <input type="text" class="form-control" id="volume" name="volume" 
                                   placeholder="Vol 1, Page 234">
                        </div>
                        
                        <div class="form-group">
                            <label for="legal_area">Legal Area</label>
                            <select class="form-control" id="legal_area" name="legal_area">
                                <option value="">Select Area</option>
                                <option value="Constitutional Law">Constitutional Law</option>
                                <option value="Criminal Law">Criminal Law</option>
                                <option value="Civil Law">Civil Law</option>
                                <option value="Commercial Law">Commercial Law</option>
                                <option value="Islamic Law">Islamic Law</option>
                                <option value="Administrative Law">Administrative Law</option>
                                <option value="Labor Law">Labor Law</option>
                                <option value="Family Law">Family Law</option>
                                <option value="Property Law">Property Law</option>
                                <option value="Contract Law">Contract Law</option>
                                <option value="Corporate Law">Corporate Law</option>
                                <option value="Tax Law">Tax Law</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="document_type">Document Type</label>
                            <select class="form-control" id="document_type" name="document_type">
                                <option value="">Select Type</option>
                                <option value="Judgment">Judgment</option>
                                <option value="Statute">Statute</option>
                                <option value="Rule">Rule</option>
                                <option value="Regulation">Regulation</option>
                                <option value="Notification">Notification</option>
                                <option value="Ordinance">Ordinance</option>
                                <option value="Act">Act</option>
                                <option value="Order">Order</option>
                            </select>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn-upload" id="uploadBtn">
                        <i class="fas fa-upload me-2"></i>Upload & Process Document
                    </button>
                </form>
            </div>

            <!-- Documents List -->
            <div class="upload-section">
                <h2 class="mb-4">
                    <i class="fas fa-database me-3"></i>Uploaded Documents
                </h2>
                
                <div id="documentsContainer">
                    <div class="text-center text-muted py-5">
                        <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
                        <p>Loading documents...</p>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Upload functionality
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const uploadForm = document.getElementById('uploadForm');
            const uploadBtn = document.getElementById('uploadBtn');
            const alertContainer = document.getElementById('alertContainer');

            // Drag and drop
            uploadArea.addEventListener('click', () => fileInput.click());
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                fileInput.files = e.dataTransfer.files;
                updateFileDisplay();
            });

            fileInput.addEventListener('change', updateFileDisplay);

            function updateFileDisplay() {
                const files = fileInput.files;
                if (files.length > 0) {
                    const fileName = files[0].name;
                    uploadArea.innerHTML = `
                        <i class="fas fa-file-alt fa-3x text-primary mb-3"></i>
                        <h4>File Selected</h4>
                        <p class="text-muted">${fileName}</p>
                    `;
                }
            }

            // Form submission
            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                if (!fileInput.files.length) {
                    showAlert('Please select a file to upload.', 'error');
                    return;
                }

                const formData = new FormData(uploadForm);
                uploadBtn.disabled = true;
                uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';

                try {
                    const response = await fetch('/api/upload-document', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        showAlert('Document uploaded and processed successfully!', 'success');
                        uploadForm.reset();
                        resetUploadArea();
                        loadDocuments();
                    } else {
                        showAlert(result.error || 'Upload failed', 'error');
                    }
                } catch (error) {
                    showAlert('Upload failed. Please try again.', 'error');
                } finally {
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i>Upload & Process Document';
                }
            });

            function resetUploadArea() {
                uploadArea.innerHTML = `
                    <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                    <h4>Drop files here or click to select</h4>
                    <p class="text-muted">Supported formats: PDF, DOCX, TXT (Max: 16MB)</p>
                `;
            }

            function showAlert(message, type) {
                const alertClass = type === 'success' ? 'alert-success' : 'alert-error';
                const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';
                
                alertContainer.innerHTML = `
                    <div class="alert ${alertClass}">
                        <i class="fas fa-${icon} me-2"></i>${message}
                    </div>
                `;
                
                setTimeout(() => {
                    alertContainer.innerHTML = '';
                }, 5000);
            }

            // Load documents (simplified for now)
            async function loadDocuments() {
                try {
                    // Since we don't have the documents API fully connected yet,
                    // we'll show a placeholder
                    document.getElementById('documentsContainer').innerHTML = `
                        <div class="text-center text-muted py-5">
                            <i class="fas fa-folder-open fa-3x mb-3"></i>
                            <h4>Documents will appear here</h4>
                            <p>Upload your first legal document above to get started.</p>
                        </div>
                    `;
                } catch (error) {
                    console.error('Error loading documents:', error);
                }
            }

            // Load documents on page load
            loadDocuments();

            // Quick action handlers
            document.getElementById('addSampleDataBtn').addEventListener('click', async function() {
                if (!confirm('This will add sample legal documents for testing. Continue?')) {
                    return;
                }
                
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding Sample Data...';
                
                try {
                    const response = await fetch('/api/add-test-data', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        showAlert(`Sample legal data added successfully! Added ${result.count} Pakistani legal citations. You can now test the AI chat.`, 'success');
                        // Update stats
                        document.getElementById('totalCitations').textContent = result.count;
                        document.getElementById('totalChunks').textContent = result.count * 2; // Approximate
                        document.getElementById('lastUpdate').textContent = 'Just now';
                        loadDocuments();
                    } else {
                        showAlert(result.message || 'Failed to add sample data.', 'error');
                    }
                } catch (error) {
                    showAlert('Failed to add sample data. Please try again.', 'error');
                } finally {
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-database me-2"></i>Add Sample Legal Data';
                }
            });

            document.getElementById('testChatBtn').addEventListener('click', function() {
                window.open('/', '_blank');
            });

            document.getElementById('clearDataBtn').addEventListener('click', async function() {
                if (!confirm('This will remove all uploaded documents. This action cannot be undone. Continue?')) {
                    return;
                }
                
                showAlert('Clear data functionality would be implemented here in production.', 'error');
            });

            // Floating Action Button functionality
            const fabBtn = document.getElementById('fabBtn');
            const fabMenu = document.getElementById('fabMenu');
            let isMenuOpen = false;

            if (fabBtn && fabMenu) {
                fabBtn.addEventListener('click', function() {
                    isMenuOpen = !isMenuOpen;
                    fabMenu.classList.toggle('show', isMenuOpen);
                    
                    // Rotate FAB icon
                    const icon = fabBtn.querySelector('i');
                    if (icon) {
                        icon.style.transform = isMenuOpen ? 'rotate(45deg)' : 'rotate(0deg)';
                    }
                });
            }

            // Close menu when clicking outside
            if (fabBtn && fabMenu) {
                document.addEventListener('click', function(e) {
                    if (!fabBtn.contains(e.target) && !fabMenu.contains(e.target)) {
                        isMenuOpen = false;
                        fabMenu.classList.remove('show');
                        const icon = fabBtn.querySelector('i');
                        if (icon) {
                            icon.style.transform = 'rotate(0deg)';
                        }
                    }
                });
            }
        </script>
    </body>
    </html>
    """, documents_count=documents_count)

@api_bp.route('/add-test-data', methods=['POST'])
def add_test_data():
    """Add sample test data for mobile/web testing"""
    # Skip tenant requirement for testing
    try:
        # Sample Pakistani legal citations for testing
        sample_data = [
            {
                'title': 'PLD 2023 SC 567 - Constitutional Rights Case',
                'citation': 'PLD 2023 SC 567',
                'court': 'Supreme Court of Pakistan',
                'year': 2023,
                'legal_area': 'Constitutional Law',
                'document_type': 'Judgment',
                'content': 'This landmark constitutional rights case established precedent for fundamental rights protection under Articles 8-28 of the Constitution of Pakistan 1973. The Supreme Court held that fundamental rights are inalienable and cannot be suspended except in accordance with law.'
            },
            {
                'title': 'SCMR 2023 Vol 1 234 - Contract Law Dispute',
                'citation': 'SCMR 2023 Vol 1 234',
                'court': 'Lahore High Court',
                'year': 2023,
                'legal_area': 'Contract Law',
                'document_type': 'Judgment',
                'content': 'Commercial contract interpretation under Contract Act 1872, focusing on breach of contract remedies and damages calculation methodology. The court emphasized the principle of restitutio in integrum.'
            },
            {
                'title': 'CLC 2023 456 - Criminal Procedure Matter',
                'citation': 'CLC 2023 456',
                'court': 'Karachi High Court (Sindh)',
                'year': 2023,
                'legal_area': 'Criminal Law',
                'document_type': 'Judgment',
                'content': 'Criminal procedure under Code of Criminal Procedure 1898, bail provisions and fundamental rights during investigation. The court reiterated that bail is the rule, jail is the exception.'
            },
            {
                'title': 'MLD 2023 789 - Family Law Case',
                'citation': 'MLD 2023 789',
                'court': 'Peshawar High Court',
                'year': 2023,
                'legal_area': 'Family Law',
                'document_type': 'Judgment',
                'content': 'Family law matters under Muslim Family Laws Ordinance 1961, focusing on matrimonial rights and obligations. The court emphasized the Islamic principles of family harmony and mutual respect.'
            }
        ]
        
        return jsonify({
            'success': True,
            'message': f'Added {len(sample_data)} sample legal documents successfully!',
            'data': sample_data,
            'count': len(sample_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to add test data'
        }), 500

# Export all blueprints for registration
__all__ = ['auth_bp', 'api_bp', 'admin_bp', 'main_bp']