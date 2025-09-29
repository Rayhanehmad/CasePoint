"""
Configuration classes for different environments
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///kanoonpk.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
    
    # Docker and OCR settings
    DOCKER_VOLUMES_PATH = os.environ.get('DOCKER_VOLUMES_PATH') or '/docker_volumes'
    OCR_ENABLED = True
    OCR_LANGUAGE = 'eng'  # Default Tesseract language
    OCR_CONFIG = '--psm 6'  # Page segmentation mode for documents
    
    # External service settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CHROMA_DB_PATH = os.environ.get('CHROMA_DB_PATH') or 'chroma_db'
    
    # Stripe settings
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Application settings
    ITEMS_PER_PAGE = 20
    SEARCH_RESULTS_PER_PAGE = 10
    MAX_SEARCH_RESULTS = 100
    
    # Rate limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_DEFAULT = "100 per hour"
    RATE_LIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    
    # Multi-tenancy settings
    DEFAULT_TENANT_PLAN = 'free'
    MAX_TENANTS_PER_USER = 5
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DEVELOPMENT = True
    
    # Override database requirement for development - use existing DATABASE_URL
    def __init__(self):
        # Don't call parent __init__ to avoid DATABASE_URL requirement
        pass
    
    # Relaxed rate limiting for development
    RATE_LIMIT_DEFAULT = "1000 per hour"
    
    # Enable SQL query logging
    SQLALCHEMY_ECHO = False  # Reduce noise in development
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Development specific logging
        import logging
        logging.basicConfig(level=logging.DEBUG)

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Force HTTPS
    PREFERRED_URL_SCHEME = 'https'
    
    # Enforce required environment variables
    def __init__(self):
        super().__init__()
        required_vars = ['SESSION_SECRET', 'JWT_SECRET_KEY', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production logging to file
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/kanoonpk.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('KanoonPK Production Startup')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Disable rate limiting for testing
    RATE_LIMIT_ENABLED = False
    
    # Fast JWT expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}