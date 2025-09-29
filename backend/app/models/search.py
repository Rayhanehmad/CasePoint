"""
Search log model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

class SearchLog(Base):
    __tablename__ = "search_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    search_type = Column(String(50), nullable=False)  # basic, advanced, ai_advanced
    filters = Column(JSONB)
    results_count = Column(Integer)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="search_logs")
    
    def __repr__(self):
        return f"<SearchLog {self.search_type}: {self.query[:50]}>"