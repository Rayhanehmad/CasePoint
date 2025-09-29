"""
Base model with common functionality
"""
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app import db

class BaseModel(db.Model):
    """Base model with common fields and functionality"""
    __abstract__ = True
    
    # Primary key as UUID for better security and scalability
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self, exclude=None):
        """Convert model to dictionary"""
        exclude = exclude or []
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                result[column.name] = value
        return result
    
    def update(self, **kwargs):
        """Update model with kwargs"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        return self
    
    def soft_delete(self):
        """Soft delete the record"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        return self
    
    @classmethod
    def active(cls):
        """Query only non-deleted records"""
        return cls.query.filter(cls.is_deleted == False)
    
    def save(self):
        """Save the model to database"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Hard delete the record"""
        db.session.delete(self)
        db.session.commit()

class TenantMixin:
    """Mixin for tenant-aware models"""
    
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenant.id'), nullable=False, index=True)
    
    @classmethod
    def for_tenant(cls, tenant_id):
        """Query records for specific tenant"""
        return cls.active().filter(cls.tenant_id == tenant_id)
    
    @classmethod
    def current_tenant(cls):
        """Query records for current tenant"""
        from flask import g
        if hasattr(g, 'tenant') and g.tenant:
            return cls.for_tenant(g.tenant.id)
        return cls.query.filter(False)  # Return empty query