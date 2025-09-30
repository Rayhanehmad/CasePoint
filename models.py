"""
Database models for KanoonPK
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class LegalCitation(db.Model):
    """Legal Citation/Case model for storing Pakistan law cases"""
    __tablename__ = 'legal_citations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Case Information
    title = db.Column(db.String(500), nullable=False, index=True)
    citation = db.Column(db.String(255), nullable=False, unique=True, index=True)
    court = db.Column(db.String(100), index=True)
    jurisdiction = db.Column(db.String(100), index=True)
    date_decided = db.Column(db.Date, index=True)
    year = db.Column(db.Integer, index=True)
    
    # Legal Details
    legal_area = db.Column(db.String(100), index=True)  # Criminal, Civil, Constitutional, etc.
    case_type = db.Column(db.String(50))  # Appeal, Writ, Review, etc.
    judges = db.Column(db.Text)  # Comma-separated judge names
    
    # Content
    summary = db.Column(db.Text)
    full_text = db.Column(db.Text)
    headnotes = db.Column(db.Text)
    keywords = db.Column(db.Text)  # Comma-separated keywords
    
    # References
    citations_referred = db.Column(db.Text)  # Citations mentioned in judgment
    statutes_referred = db.Column(db.Text)  # Statutes/Acts mentioned
    
    # File Information (if uploaded as document)
    file_path = db.Column(db.String(500))
    file_type = db.Column(db.String(20))
    ocr_confidence = db.Column(db.Float)
    
    # Metadata
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ChromaDB vector ID for similarity search
    vector_id = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<LegalCitation {self.citation}>'
    
    def to_dict(self):
        """Convert citation to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'citation': self.citation,
            'court': self.court,
            'jurisdiction': self.jurisdiction,
            'date_decided': self.date_decided.isoformat() if self.date_decided else None,
            'year': self.year,
            'legal_area': self.legal_area,
            'case_type': self.case_type,
            'judges': self.judges,
            'summary': self.summary,
            'keywords': self.keywords,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class User(db.Model):
    """User model with authentication support"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def is_online(self):
        """Check if user is currently online (active in last 5 minutes)"""
        if not self.last_seen:
            return False
        return (datetime.utcnow() - self.last_seen).total_seconds() < 300
    
    def to_dict(self):
        """Convert user to dictionary (excluding password)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_online': self.is_online()
        }
    
    # Relationship to uploaded citations
    citations = db.relationship('LegalCitation', backref='uploader', lazy=True, foreign_keys='LegalCitation.uploaded_by')