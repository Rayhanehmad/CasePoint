"""
SaaS Routes and API endpoints for KanoonPK Legal Research Platform
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, g, session
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
    db, Tenant, User, Subscription, UsageMetric, LegalDocument, QueryHistory, LegalWorkspace,
    create_tenant_schema, record_usage, PLAN_LIMITS
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
        return render_template('auth/register_tenant.html')
    
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
            plan='free',
            **PLAN_LIMITS['free']
        )
        db.session.add(tenant)
        db.session.flush()  # Get tenant ID
        
        # Create tenant schema
        if not create_tenant_schema(tenant.id):
            raise Exception("Failed to create tenant schema")
        
        # Create admin user
        admin_user = User(
            email=data['admin_email'],
            first_name=data['admin_first_name'],
            last_name=data['admin_last_name'],
            tenant_id=tenant.id,
            role='owner',
            is_verified=True
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
        return render_template('auth/login.html')
    
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

@main_bp.route('/')
@require_tenant
def home():
    """Main chat interface"""
    return render_template('saas/dashboard.html', 
                         tenant=g.tenant,
                         user=current_user if current_user.is_authenticated else None)

@main_bp.route('/dashboard')
@login_required
@require_tenant
def dashboard():
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
@login_required
@require_tenant
@require_usage_limit('document_upload')
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
        doc_manager = TenantDocumentManager(g.tenant.id)
        result = doc_manager.upload_document(file, current_user.id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'document_id': result['document_id'],
                'chunks_processed': result['chunks_processed'],
                'document_type': result['document_type'],
                'legal_areas': result['legal_areas'],
                'message': 'Document uploaded and processed successfully'
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        return jsonify({'error': 'Upload failed. Please try again.'}), 500

@api_bp.route('/documents', methods=['GET'])
@login_required
@require_tenant
def list_documents():
    """List tenant's uploaded documents"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    documents = LegalDocument.query.filter_by(processing_status='processed')\
                                  .order_by(LegalDocument.created_at.desc())\
                                  .paginate(page=page, per_page=per_page, error_out=False)
    
    doc_list = []
    for doc in documents.items:
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
    
    return jsonify({
        'documents': doc_list,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': documents.total,
            'pages': documents.pages,
            'has_next': documents.has_next,
            'has_prev': documents.has_prev
        }
    })

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

# Export all blueprints for registration
__all__ = ['auth_bp', 'api_bp', 'admin_bp', 'main_bp']