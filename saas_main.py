"""
Main Application Entry Point for KanoonPK SaaS Legal Research Platform
"""
import os
import logging
from flask import Flask, render_template_string
from flask_migrate import Migrate

# Import our modular components
from models import db, create_tenant_schema, PLAN_LIMITS
from saas_app import (
    app as base_app, jwt, login_manager, 
    EnhancedLegalSearchEngine, TenantDocumentManager, client
)
from saas_routes import auth_bp, api_bp, admin_bp, main_bp
from saas_templates import render_template_content

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_app():
    """Create and configure the Flask application"""
    
    # Use the base app from saas_app.py
    app = base_app
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    
    # Register chat interface
    from chat_interface import chat_bp
    app.register_blueprint(chat_bp)
    
    # Initialize database migration
    migrate = Migrate(app, db)
    
    # Create database tables
    with app.app_context():
        try:
            # Create all public schema tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Create default plans data if needed
            from models import Tenant, User
            
            # Check if we need to create sample data
            if Tenant.query.count() == 0:
                logger.info("No tenants found. Database is ready for new registrations.")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    # =============================================================================
    # CUSTOM TEMPLATE RENDERING
    # =============================================================================
    
    @app.route('/auth/register-tenant', methods=['GET'])
    def register_tenant_page():
        return render_template_string(render_template_content('auth/register_tenant.html'))
    
    @app.route('/auth/login', methods=['GET'])
    def login_page():
        return render_template_string(render_template_content('auth/login.html'))
    
    # Override the main route to use our custom dashboard  
    @app.route('/', endpoint='public_home')
    def home():
        from flask import g
        from flask_login import current_user
        
        # If no tenant context, show landing page
        if not hasattr(g, 'tenant'):
            return render_template_string("""
            <!DOCTYPE html>
            <html lang="en" data-bs-theme="dark">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>KanoonPK SaaS - Legal Research Platform</title>
                <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
                <style>
                    .hero-section {
                        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                    }
                    .feature-card {
                        transition: transform 0.2s;
                        border: none;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }
                    .feature-card:hover {
                        transform: translateY(-5px);
                    }
                </style>
            </head>
            <body>
                <div class="hero-section">
                    <div class="container">
                        <div class="row align-items-center">
                            <div class="col-lg-6 text-white">
                                <i class="fas fa-balance-scale fa-5x mb-4"></i>
                                <h1 class="display-3 fw-bold mb-3">KanoonPK SaaS</h1>
                                <h2 class="h4 mb-4">AI-Powered Legal Research Platform for Pakistan Law</h2>
                                <p class="lead mb-5">Transform your legal research with Pakistan's most advanced AI-powered platform. Multi-tenant architecture for law firms, legal departments, and legal professionals.</p>
                                <div class="d-flex gap-3 flex-wrap">
                                    <a href="/auth/register-tenant" class="btn btn-primary btn-lg">
                                        <i class="fas fa-building me-2"></i>Start Free Trial
                                    </a>
                                    <a href="/auth/login" class="btn btn-outline-light btn-lg">
                                        <i class="fas fa-sign-in-alt me-2"></i>Login
                                    </a>
                                </div>
                            </div>
                            <div class="col-lg-6 mt-5 mt-lg-0">
                                <div class="row g-4">
                                    <div class="col-md-6">
                                        <div class="card feature-card h-100 bg-light">
                                            <div class="card-body text-center">
                                                <i class="fas fa-search fa-3x text-primary mb-3"></i>
                                                <h5>Advanced Legal Search</h5>
                                                <p class="text-muted small">AI-powered search through Pakistan legal database with smart filters</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="card feature-card h-100 bg-light">
                                            <div class="card-body text-center">
                                                <i class="fas fa-users fa-3x text-success mb-3"></i>
                                                <h5>Team Collaboration</h5>
                                                <p class="text-muted small">Shared workspaces for collaborative legal research</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="card feature-card h-100 bg-light">
                                            <div class="card-body text-center">
                                                <i class="fas fa-gavel fa-3x text-warning mb-3"></i>
                                                <h5>Precedent Analysis</h5>
                                                <p class="text-muted small">Find similar cases and legal precedents automatically</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="card feature-card h-100 bg-light">
                                            <div class="card-body text-center">
                                                <i class="fas fa-chart-line fa-3x text-info mb-3"></i>
                                                <h5>Usage Analytics</h5>
                                                <p class="text-muted small">Track research patterns and team productivity</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Plans Section -->
                        <div class="row mt-5 pt-5">
                            <div class="col-12 text-center text-white mb-4">
                                <h3>Choose Your Plan</h3>
                                <p class="lead">Flexible pricing for every organization size</p>
                            </div>
                            <div class="col-md-3">
                                <div class="card">
                                    <div class="card-header bg-secondary text-white text-center">
                                        <h5>Free</h5>
                                        <h6>$0/month</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled">
                                            <li>✓ 100 queries/month</li>
                                            <li>✓ 10 documents</li>
                                            <li>✓ 1 user</li>
                                            <li>✓ Basic search</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card border-primary">
                                    <div class="card-header bg-primary text-white text-center">
                                        <h5>Lawyer</h5>
                                        <h6>$29/month</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled">
                                            <li>✓ 1,000 queries/month</li>
                                            <li>✓ 100 documents</li>
                                            <li>✓ 3 users</li>
                                            <li>✓ Advanced search & precedents</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card">
                                    <div class="card-header bg-success text-white text-center">
                                        <h5>Firm</h5>
                                        <h6>$99/month</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled">
                                            <li>✓ 5,000 queries/month</li>
                                            <li>✓ 500 documents</li>
                                            <li>✓ 15 users</li>
                                            <li>✓ Team analytics & API</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card">
                                    <div class="card-header bg-warning text-dark text-center">
                                        <h5>Enterprise</h5>
                                        <h6>Custom</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled">
                                            <li>✓ Unlimited queries</li>
                                            <li>✓ Unlimited documents</li>
                                            <li>✓ Unlimited users</li>
                                            <li>✓ Custom integrations</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        # Tenant context exists, show dashboard
        if current_user.is_authenticated:
            # Get usage data for dashboard
            from datetime import datetime
            from models import QueryHistory, LegalDocument, UsageMetric
            
            current_month = datetime.utcnow().strftime('%Y-%m')
            query_usage = g.tenant.get_current_usage('query', current_month)
            doc_usage = g.tenant.get_current_usage('document_upload')
            
            # Get recent queries and documents
            recent_queries = QueryHistory.query.filter_by(user_id=current_user.id)\
                                              .order_by(QueryHistory.created_at.desc())\
                                              .limit(10).all()
            
            recent_docs = LegalDocument.query.filter_by(upload_user_id=current_user.id)\
                                            .order_by(LegalDocument.created_at.desc())\
                                            .limit(5).all()
            
            return render_template_string(
                render_template_content('saas/dashboard.html'),
                tenant=g.tenant,
                user=current_user,
                query_usage=query_usage,
                doc_usage=doc_usage,
                recent_queries=recent_queries,
                recent_docs=recent_docs,
                plan_limits=PLAN_LIMITS[g.tenant.plan]
            )
        else:
            # Redirect to login for existing tenant
            from flask import redirect, url_for
            return redirect(url_for('auth.login'))
    
    # =============================================================================
    # HEALTH CHECK AND STATUS ENDPOINTS
    # =============================================================================
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            
            # Test OpenAI connection (optional)
            openai_status = "connected" if os.getenv("OPENAI_API_KEY") else "no_api_key"
            
            return {
                'status': 'healthy',
                'database': 'connected',
                'openai': openai_status,
                'features': {
                    'multi_tenant': True,
                    'legal_search': True,
                    'document_upload': True,
                    'collaboration': True
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}, 500
    
    @app.route('/api/features')
    def list_features():
        """List available features for current tenant plan"""
        from flask import g, jsonify
        from flask_login import current_user
        
        if not hasattr(g, 'tenant'):
            return jsonify({'error': 'No tenant context'}), 400
        
        plan_features = PLAN_LIMITS.get(g.tenant.plan, {}).get('features', [])
        
        feature_descriptions = {
            'basic_search': 'Basic legal document search',
            'advanced_search': 'Advanced search with filters and precedent analysis',
            'document_upload': 'Upload and index legal documents',
            'pdf_export': 'Export research results as PDF',
            'citation_analysis': 'Automatic legal citation extraction and formatting',
            'precedent_matching': 'Find similar cases and legal precedents',
            'workspace_collaboration': 'Shared workspaces for team collaboration',
            'team_analytics': 'Usage analytics and team performance metrics',
            'custom_exports': 'Advanced export options and formatting',
            'api_access': 'RESTful API access for integrations',
            'all_features': 'All platform features included',
            'priority_support': 'Priority customer support',
            'custom_integrations': 'Custom integration development',
            'sso': 'Single Sign-On integration'
        }
        
        available_features = []
        for feature in plan_features:
            if feature == 'all_features':
                available_features = list(feature_descriptions.keys())
                break
            elif feature.startswith('all_'):
                # Include all features from lower tier
                base_features = []
                if feature == 'all_lawyer_features':
                    base_features = PLAN_LIMITS['lawyer']['features']
                available_features.extend(base_features)
            else:
                available_features.append(feature)
        
        return jsonify({
            'tenant_plan': g.tenant.plan,
            'available_features': available_features,
            'feature_descriptions': {f: feature_descriptions.get(f, f) for f in available_features}
        })
    
    # =============================================================================
    # ERROR HANDLERS
    # =============================================================================
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en" data-bs-theme="dark">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>404 - Page Not Found | KanoonPK SaaS</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <div class="container-fluid vh-100 d-flex align-items-center justify-content-center">
                <div class="text-center">
                    <i class="fas fa-gavel fa-4x text-muted mb-4"></i>
                    <h1 class="display-4">404</h1>
                    <p class="lead">Page not found in our legal database</p>
                    <a href="/" class="btn btn-primary">
                        <i class="fas fa-home me-2"></i>Return to Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """), 404
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en" data-bs-theme="dark">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>500 - Server Error | KanoonPK SaaS</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <div class="container-fluid vh-100 d-flex align-items-center justify-content-center">
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle fa-4x text-warning mb-4"></i>
                    <h1 class="display-4">500</h1>
                    <p class="lead">Internal server error occurred</p>
                    <p class="text-muted">Our legal experts are working on a solution</p>
                    <a href="/" class="btn btn-primary">
                        <i class="fas fa-refresh me-2"></i>Try Again
                    </a>
                </div>
            </div>
        </body>
        </html>
        """), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en" data-bs-theme="dark">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>403 - Access Denied | KanoonPK SaaS</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <div class="container-fluid vh-100 d-flex align-items-center justify-content-center">
                <div class="text-center">
                    <i class="fas fa-shield-alt fa-4x text-danger mb-4"></i>
                    <h1 class="display-4">403</h1>
                    <p class="lead">Access denied</p>
                    <p class="text-muted">You don't have permission to access this resource</p>
                    <a href="/" class="btn btn-primary">
                        <i class="fas fa-home me-2"></i>Return to Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """), 403
    
    return app

# =============================================================================
# APPLICATION INSTANCE
# =============================================================================

# Create the application instance
app = create_app()

# =============================================================================
# CLI COMMANDS FOR DATABASE MANAGEMENT
# =============================================================================

@app.cli.command()
def init_db():
    """Initialize the database with tables and sample data"""
    try:
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Check if we need sample data
        from models import Tenant
        if Tenant.query.count() == 0:
            print("📝 Database ready for tenant registrations")
        else:
            print(f"📊 Found {Tenant.query.count()} existing tenants")
            
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

@app.cli.command()
def create_sample_tenant():
    """Create a sample tenant for testing"""
    try:
        from models import Tenant, User, create_tenant_schema
        
        # Create sample tenant
        tenant = Tenant(
            name="Sample Law Firm",
            subdomain="sample",
            plan="lawyer",
            **PLAN_LIMITS['lawyer']
        )
        db.session.add(tenant)
        db.session.flush()
        
        # Create tenant schema
        create_tenant_schema(tenant.id)
        
        # Create admin user
        admin = User(
            email="admin@sample.com",
            first_name="Admin",
            last_name="User",
            tenant_id=tenant.id,
            role="owner",
            is_verified=True
        )
        admin.set_password("password123")
        db.session.add(admin)
        
        db.session.commit()
        
        print(f"✅ Sample tenant created:")
        print(f"   Organization: {tenant.name}")
        print(f"   Subdomain: {tenant.subdomain}")
        print(f"   Admin email: {admin.email}")
        print(f"   Admin password: password123")
        print(f"   Access URL: http://{tenant.subdomain}.localhost:5000")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Sample tenant creation failed: {e}")

@app.cli.command()
def list_tenants():
    """List all tenants"""
    try:
        from models import Tenant, User
        
        tenants = Tenant.query.all()
        if not tenants:
            print("No tenants found")
            return
        
        print(f"Found {len(tenants)} tenants:")
        print("-" * 80)
        
        for tenant in tenants:
            user_count = User.query.filter_by(tenant_id=tenant.id).count()
            print(f"Name: {tenant.name}")
            print(f"Subdomain: {tenant.subdomain}")
            print(f"Plan: {tenant.plan}")
            print(f"Status: {tenant.status}")
            print(f"Users: {user_count}")
            print(f"Created: {tenant.created_at}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Error listing tenants: {e}")

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )