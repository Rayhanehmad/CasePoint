"""
Tenant and multi-tenancy models
"""
from enum import Enum
from sqlalchemy.dialects.postgresql import UUID, JSON
from app import db
from app.models.base import BaseModel

class TenantStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"

class Tenant(BaseModel):
    """Enhanced tenant model for SaaS platform"""
    
    # Basic information
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(50), nullable=False, unique=True, index=True)
    custom_domain = db.Column(db.String(100), nullable=True, unique=True)
    
    # Contact information
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Address
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    
    # Status and configuration
    status = db.Column(db.Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Plan and limits
    plan_id = db.Column(UUID(as_uuid=True), db.ForeignKey('plan.id'), nullable=True)
    trial_ends_at = db.Column(db.DateTime, nullable=True)
    
    # Settings
    settings = db.Column(JSON, default=dict)
    features = db.Column(JSON, default=dict)
    
    # Usage tracking
    current_users = db.Column(db.Integer, default=0)
    current_documents = db.Column(db.Integer, default=0)
    current_storage_mb = db.Column(db.Integer, default=0)
    monthly_searches = db.Column(db.Integer, default=0)
    
    # Relationships
    users = db.relationship('TenantUser', backref='tenant', lazy='dynamic')
    subscription = db.relationship('Subscription', backref='tenant', uselist=False)
    legal_documents = db.relationship('LegalDocument', backref='tenant', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tenant {self.name}>'
    
    @property
    def is_trial(self):
        """Check if tenant is in trial period"""
        return self.status == TenantStatus.TRIAL
    
    @property
    def trial_expired(self):
        """Check if trial has expired"""
        if not self.trial_ends_at:
            return False
        from datetime import datetime
        return datetime.utcnow() > self.trial_ends_at
    
    def get_plan_limits(self):
        """Get current plan limits"""
        if self.plan_id and self.subscription:
            return self.subscription.plan.limits
        # Default trial limits
        return {
            'max_users': 3,
            'max_documents': 100,
            'max_storage_mb': 1000,
            'max_monthly_searches': 500,
            'features': ['basic_search', 'document_upload']
        }
    
    def can_add_user(self):
        """Check if tenant can add more users"""
        limits = self.get_plan_limits()
        return self.current_users < limits.get('max_users', 0)
    
    def can_upload_document(self, file_size_mb=0):
        """Check if tenant can upload documents"""
        limits = self.get_plan_limits()
        
        # Check document count limit
        if self.current_documents >= limits.get('max_documents', 0):
            return False
        
        # Check storage limit
        if (self.current_storage_mb + file_size_mb) > limits.get('max_storage_mb', 0):
            return False
        
        return True
    
    def can_perform_search(self):
        """Check if tenant can perform searches"""
        limits = self.get_plan_limits()
        return self.monthly_searches < limits.get('max_monthly_searches', 0)
    
    def has_feature(self, feature_name):
        """Check if tenant has access to specific feature"""
        limits = self.get_plan_limits()
        return feature_name in limits.get('features', [])
    
    def increment_usage(self, metric, amount=1):
        """Increment usage metric"""
        if hasattr(self, f'current_{metric}'):
            current_value = getattr(self, f'current_{metric}')
            setattr(self, f'current_{metric}', current_value + amount)
            self.save()

class TenantUser(BaseModel):
    """Association between tenants and users with roles"""
    
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenant.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    
    # Role within the tenant
    role = db.Column(db.String(50), nullable=False, default='member')
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    invited_at = db.Column(db.DateTime, nullable=True)
    joined_at = db.Column(db.DateTime, nullable=True)
    
    # Permissions
    permissions = db.Column(JSON, default=dict)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'user_id', name='unique_tenant_user'),
    )
    
    def __repr__(self):
        return f'<TenantUser {self.user_id} in {self.tenant_id}>'
    
    @property
    def is_owner(self):
        return self.role == 'owner'
    
    @property
    def is_admin(self):
        return self.role in ['owner', 'admin']
    
    def has_permission(self, permission):
        """Check if user has specific permission in this tenant"""
        if self.is_owner:
            return True
        return permission in self.permissions.get('allowed', [])