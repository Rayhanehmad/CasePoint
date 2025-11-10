"""Shared Excerpt model for storing shareable legal document excerpts"""

import uuid
import hashlib
from datetime import datetime, timedelta
from models import db


class SharedExcerpt(db.Model):
    """Model for storing shareable excerpts from legal citations"""
    __tablename__ = 'shared_excerpts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Unique share code for URL
    share_code = db.Column(db.String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    
    # Reference to original citation
    citation_id = db.Column(db.Integer, db.ForeignKey('legal_citations.id', ondelete='CASCADE'), nullable=False, index=True)
    citation = db.relationship('LegalCitation', backref='shared_excerpts')
    
    # Excerpt content
    excerpt_text = db.Column(db.Text, nullable=False)
    excerpt_hash = db.Column(db.String(64), nullable=False, index=True)  # SHA256 hash for deduplication
    excerpt_start_pos = db.Column(db.Integer)  # Position in full text (optional)
    excerpt_length = db.Column(db.Integer)  # Length of excerpt (optional)
    
    # Lifecycle management
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)  # Optional expiration
    is_revoked = db.Column(db.Boolean, default=False, nullable=False)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Required: authenticated users only
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Usage tracking
    view_count = db.Column(db.Integer, default=0)
    last_viewed = db.Column(db.DateTime, nullable=True)
    
    # Optional: allow creator to add context/notes
    notes = db.Column(db.Text, nullable=True)
    
    # Compound index for audit queries
    __table_args__ = (
        db.Index('idx_citation_created', 'citation_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<SharedExcerpt {self.share_code}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'share_code': self.share_code,
            'citation_id': self.citation_id,
            'excerpt_text': self.excerpt_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'view_count': self.view_count,
            'notes': self.notes,
            # Include citation info
            'citation': {
                'id': self.citation.id,
                'title': self.citation.title,
                'citation': self.citation.citation,
                'court': self.citation.court,
                'year': self.citation.year,
                'journal': self.citation.journal
            } if self.citation else None
        }
    
    @staticmethod
    def generate_excerpt_hash(text):
        """Generate SHA256 hash of normalized excerpt text"""
        normalized = ' '.join(text.strip().split())  # Normalize whitespace
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    @staticmethod
    def create_excerpt(citation_id, excerpt_text, user_id, notes=None, expiration_days=90):
        """
        Create a new shared excerpt with validation and deduplication
        
        Args:
            citation_id: ID of the citation
            excerpt_text: Selected text excerpt
            user_id: ID of the user creating the share
            notes: Optional notes/context
            expiration_days: Days until expiration (default 90, None for no expiration)
        
        Returns:
            SharedExcerpt instance or None if duplicate
        """
        # Normalize and hash excerpt
        normalized_text = ' '.join(excerpt_text.strip().split())
        excerpt_hash = SharedExcerpt.generate_excerpt_hash(normalized_text)
        
        # Check for existing excerpt (deduplication)
        existing = SharedExcerpt.query.filter_by(
            citation_id=citation_id,
            excerpt_hash=excerpt_hash,
            is_revoked=False
        ).filter(
            (SharedExcerpt.expires_at == None) | (SharedExcerpt.expires_at > datetime.utcnow())
        ).first()
        
        if existing:
            return existing  # Return existing share link
        
        # Calculate expiration
        expires_at = None
        if expiration_days:
            expires_at = datetime.utcnow() + timedelta(days=expiration_days)
        
        # Create new excerpt
        excerpt = SharedExcerpt(
            citation_id=citation_id,
            excerpt_text=normalized_text,
            excerpt_hash=excerpt_hash,
            created_by=user_id,
            notes=notes,
            expires_at=expires_at
        )
        
        db.session.add(excerpt)
        db.session.commit()
        
        return excerpt
    
    def is_valid(self):
        """Check if excerpt is valid (not revoked, not expired)"""
        if self.is_revoked:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def revoke(self):
        """Revoke this shared excerpt"""
        self.is_revoked = True
        db.session.commit()
