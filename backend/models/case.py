"""
Legal Citation/Case model for storing Pakistan law cases
"""

from datetime import datetime

# Import db from __init__.py to avoid circular import
from models import db


class LegalCitation(db.Model):
    """Legal Citation/Case model for storing Pakistan law cases"""
    __tablename__ = 'legal_citations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Document Type
    document_type = db.Column(db.String(50), nullable=False, default='case', index=True)  # 'case', 'rule', 'act', 'statute'
    
    # Case Information
    title = db.Column(db.String(500), nullable=False, index=True)
    citation = db.Column(db.String(255), nullable=False, unique=True, index=True)
    court = db.Column(db.String(100), index=True)
    jurisdiction = db.Column(db.String(100), index=True)
    date_decided = db.Column(db.Date, index=True)
    year = db.Column(db.Integer, index=True)
    journal = db.Column(db.String(50), index=True, nullable=True)  # Legal journal abbreviation (PLD, MLD, etc.)
    
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
    pdf_path = db.Column(db.String(500), nullable=True)  # Path to individual citation PDF (for multi-PDF splits)
    
    # Metadata
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage Tracking
    share_count = db.Column(db.Integer, default=0)
    embed_views = db.Column(db.Integer, default=0)
    last_shared = db.Column(db.DateTime, nullable=True)
    last_embedded = db.Column(db.DateTime, nullable=True)
    
    # ChromaDB vector ID for similarity search
    vector_id = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<LegalCitation {self.citation}>'
    
    def to_dict(self):
        """Convert citation to dictionary"""
        return {
            'id': self.id,
            'document_type': self.document_type,
            'title': self.title,
            'citation': self.citation,
            'court': self.court,
            'jurisdiction': self.jurisdiction,
            'date_decided': self.date_decided.isoformat() if self.date_decided else None,
            'year': self.year,
            'journal': self.journal,
            'legal_area': self.legal_area,
            'case_type': self.case_type,
            'judges': self.judges,
            'summary': self.summary,
            'full_text': self.full_text,
            'keywords': self.keywords,
            'pdf_path': self.pdf_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
