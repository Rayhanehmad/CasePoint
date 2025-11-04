"""
Configuration for CasePoint Flask Backend
"""

import os

class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get("SESSION_SECRET", "casepoint-dev-secret-2024")
    DEBUG = True
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # File Upload
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp', 'docx', 'doc', 'txt'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # ChromaDB
    CHROMA_DB_PATH = "chroma_db"
    
    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
