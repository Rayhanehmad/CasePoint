"""
Application configuration
"""

import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Basic app config
    APP_NAME: str = "KanoonPK SaaS"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "kanoonpk-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://kanoonpk_user:kanoonpk_secure_pass_2024@localhost:5433/kanoonpk")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6380")
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]  # Configure properly for production
    
    # File storage
    UPLOAD_DIR: str = "static/uploads"
    DOCUMENTS_DIR: str = "static/documents" 
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".jpeg", ".jpg", ".png", ".txt", ".docx"]
    
    # OCR settings
    TESSERACT_PATH: str = os.getenv("TESSERACT_PATH", "/usr/bin/tesseract")
    OCR_LANGUAGES: List[str] = ["eng", "urd"]  # English and Urdu
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4"
    
    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Docker
    DOCKER_SOCKET: str = "unix:///var/run/docker.sock"
    
    class Config:
        env_file = ".env"

settings = Settings()