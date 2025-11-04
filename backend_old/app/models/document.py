"""
Legal document model
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, BigInteger, DECIMAL, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class LegalDocument(Base):
    __tablename__ = "legal_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    citation = Column(String(255), index=True)
    jurisdiction = Column(String(100), index=True)
    court_level = Column(String(100))
    date_decided = Column(Date, index=True)
    legal_area = Column(String(100), index=True)
    document_type = Column(String(50), nullable=False)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger)
    file_hash = Column(String(64), unique=True, nullable=False)
    
    # Processed content
    extracted_text = Column(Text)
    ocr_confidence = Column(DECIMAL(5, 2))
    keywords = Column(ARRAY(String))
    citations_found = Column(ARRAY(String))
    is_processed = Column(Boolean, default=False)
    
    # Metadata
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uploader = relationship("User", back_populates="uploaded_documents")
    
    def __repr__(self):
        return f"<LegalDocument {self.citation or self.title[:50]}>"