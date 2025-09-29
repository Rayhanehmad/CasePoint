"""
KanoonPK - Modern SaaS Legal Research Platform
Application Factory Pattern Implementation
"""
import os
import logging
from flask import Flask, g, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
try:
    import redis
except ImportError:
    redis = None
    
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
    
try:
    import chromadb
except ImportError:
    chromadb = None

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()
redis_client = None
openai_client = None
chroma_client = None

def create_app(config_name='development'):
    """Application factory pattern for modern Flask SaaS"""
    
    # Create Flask app instance
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(get_config(config_name))
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Initialize external services
    initialize_services(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register middleware
    register_middleware(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Configure logging
    configure_logging(app)
    
    return app

def get_config(config_name):
    """Get configuration class based on environment"""
    from app.config import config
    return config.get(config_name, config['development'])

def initialize_extensions(app):
    """Initialize Flask extensions"""
    global db, migrate, jwt, login_manager
    
    # Database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # JWT Authentication
    jwt.init_app(app)
    
    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Proxy fix for production deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

def initialize_services(app):
    """Initialize external services (Redis, OpenAI, ChromaDB)"""
    global redis_client, openai_client, chroma_client
    
    # Redis for caching and sessions (optional)
    if redis:
        try:
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = redis.from_url(redis_url)
            redis_client.ping()  # Test connection
            app.logger.info("Redis connection established")
        except Exception as e:
            app.logger.warning(f"Redis connection failed: {e}")
            redis_client = None
    else:
        app.logger.info("Redis not available - using memory-based caching")
        redis_client = None
    
    # OpenAI for AI-powered search (optional)
    if OpenAI:
        try:
            openai_api_key = app.config.get('OPENAI_API_KEY')
            if openai_api_key:
                openai_client = OpenAI(api_key=openai_api_key)
                app.logger.info("OpenAI client initialized")
            else:
                app.logger.info("OpenAI API key not configured")
                openai_client = None
        except Exception as e:
            app.logger.warning(f"OpenAI initialization failed: {e}")
            openai_client = None
    else:
        app.logger.info("OpenAI not available")
        openai_client = None
    
    # ChromaDB for vector search (optional)
    if chromadb:
        try:
            chroma_path = app.config.get('CHROMA_DB_PATH', 'chroma_db')
            chroma_client = chromadb.PersistentClient(path=chroma_path)
            app.logger.info("ChromaDB client initialized")
        except Exception as e:
            app.logger.warning(f"ChromaDB initialization failed: {e}")
            chroma_client = None
    else:
        app.logger.info("ChromaDB not available")
        chroma_client = None

def register_blueprints(app):
    """Register application blueprints"""
    
    # Import blueprints (routes are imported in blueprint modules)
    from app.main import main_bp
    from app.auth import auth_bp
    from app.api import api_bp
    from app.admin import admin_bp
    from app.billing import billing_bp
    from app.search import search_bp
    from app.analytics import analytics_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')

def register_middleware(app):
    """Register middleware functions"""
    
    # Setup bulletproof multi-tenant isolation first
    from app.core.tenant import setup_bulletproof_tenant_isolation
    setup_bulletproof_tenant_isolation(app)
    
    @app.before_request
    def load_tenant_context():
        """Load tenant context from subdomain or header"""
        from app.core.tenant import TenantManager
        TenantManager.load_tenant_context()
    
    @app.teardown_appcontext
    def reset_tenant_context(exception):
        """Reset tenant context to prevent cross-tenant leakage"""
        from app.core.tenant import TenantManager
        TenantManager.reset_tenant_context()
    
    @app.before_request
    def setup_request_logging():
        """Setup request logging and tracking"""
        import time
        g.request_start_time = time.time()
        app.logger.debug(f"Request: {request.method} {request.path}")
    
    @app.after_request
    def track_request_metrics(response):
        """Track request metrics and performance"""
        import time
        if hasattr(g, 'request_start_time'):
            duration = time.time() - g.request_start_time
            app.logger.debug(f"Request completed in {duration:.3f}s")
        return response
    
    @app.after_request
    def inject_security_headers(response):
        """Inject security headers"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template, jsonify
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template, jsonify
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template, jsonify
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403

def configure_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        # Production logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s: %(message)s'
        )
        app.logger.setLevel(logging.INFO)
        app.logger.info('KanoonPK SaaS startup')

# JWT callback functions
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader 
def user_lookup_callback(_jwt_header, jwt_data):
    from app.models import User
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()

# Flask-Login callback
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

import time