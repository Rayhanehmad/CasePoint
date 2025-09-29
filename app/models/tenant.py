"""
Tenant and multi-tenancy models
"""
from enum import Enum
from typing import List
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

class TenantVolume(BaseModel):
    """CRITICAL SECURITY: Docker volume authorization mapping for tenant isolation"""
    
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenant.id'), nullable=False)
    volume_name = db.Column(db.String(100), nullable=False, index=True)
    
    # Volume access permissions
    access_level = db.Column(db.String(20), nullable=False, default='read_only')  # read_only, read_write
    description = db.Column(db.Text, nullable=True)
    
    # Status and metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    authorized_by = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=True)
    authorized_at = db.Column(db.DateTime, nullable=True)
    
    # Volume validation metadata
    volume_type = db.Column(db.String(50), nullable=True)  # data, documents, exports, etc.
    max_size_mb = db.Column(db.Integer, nullable=True)
    
    # Security settings
    mount_options = db.Column(JSON, default=dict)  # Docker mount options
    security_tags = db.Column(JSON, default=list)  # Security classification tags
    
    # Unique constraint to prevent duplicate volume access per tenant
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'volume_name', name='unique_tenant_volume'),
        db.Index('idx_tenant_volume_active', 'tenant_id', 'is_active'),
        db.Index('idx_volume_name_active', 'volume_name', 'is_active')
    )
    
    def __repr__(self):
        return f'<TenantVolume {self.volume_name} for tenant {self.tenant_id}>'
    
    @property
    def can_write(self):
        """Check if volume allows write access"""
        return self.access_level == 'read_write'
    
    @property
    def is_authorized(self):
        """Check if volume access is properly authorized"""
        return self.is_active and self.authorized_by is not None
    
    def get_mount_options(self):
        """Get secure Docker mount options for this volume"""
        base_options = {
            'read_only': self.access_level == 'read_only',
            'no_exec': True,  # Prevent execution from volume
            'no_suid': True,  # Prevent SUID programs
            'no_dev': True    # Prevent device access
        }
        
        # Merge with custom options (custom options cannot override security)
        custom_options = self.mount_options or {}
        for key in ['read_only', 'no_exec', 'no_suid', 'no_dev']:
            if key in custom_options:
                # Security options cannot be made less restrictive
                if key == 'read_only' and base_options[key] and not custom_options[key]:
                    continue  # Cannot make read-only volume writable
                elif key in ['no_exec', 'no_suid', 'no_dev'] and base_options[key] and not custom_options[key]:
                    continue  # Cannot enable dangerous features
        
        base_options.update(custom_options)
        return base_options
    
    @classmethod
    def authorize_volume_for_tenant(cls, tenant_id: str, volume_name: str, 
                                  access_level: str = 'read_only',
                                  authorized_by: str = None) -> 'TenantVolume':
        """
        Authorize a Docker volume for a specific tenant
        
        Args:
            tenant_id: UUID of the tenant
            volume_name: Name of the Docker volume
            access_level: 'read_only' or 'read_write'
            authorized_by: UUID of the user authorizing access
            
        Returns:
            TenantVolume instance
        """
        from datetime import datetime
        
        # Validate volume name using same security rules as Docker processor
        import re
        volume_regex = re.compile(r'^[A-Za-z0-9._-]+$')
        if not volume_regex.match(volume_name):
            raise ValueError(f"Invalid volume name: {volume_name}")
        
        if access_level not in ['read_only', 'read_write']:
            raise ValueError(f"Invalid access level: {access_level}")
        
        # Check if authorization already exists
        existing = cls.query.filter_by(
            tenant_id=tenant_id,
            volume_name=volume_name
        ).first()
        
        if existing:
            # Update existing authorization
            existing.access_level = access_level
            existing.is_active = True
            existing.authorized_by = authorized_by
            existing.authorized_at = datetime.utcnow()
            return existing
        else:
            # Create new authorization
            return cls(
                tenant_id=tenant_id,
                volume_name=volume_name,
                access_level=access_level,
                is_active=True,
                authorized_by=authorized_by,
                authorized_at=datetime.utcnow()
            )
    
    @classmethod
    def revoke_volume_access(cls, tenant_id: str, volume_name: str):
        """Revoke volume access for a tenant"""
        authorization = cls.query.filter_by(
            tenant_id=tenant_id,
            volume_name=volume_name
        ).first()
        
        if authorization:
            authorization.is_active = False
    
    @classmethod
    def get_tenant_volumes(cls, tenant_id: str, active_only: bool = True) -> List['TenantVolume']:
        """Get all authorized volumes for a tenant"""
        query = cls.query.filter_by(tenant_id=tenant_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @classmethod
    def is_volume_authorized(cls, tenant_id: str, volume_name: str) -> bool:
        """Check if a tenant is authorized to access a specific volume"""
        authorization = cls.query.filter_by(
            tenant_id=tenant_id,
            volume_name=volume_name,
            is_active=True
        ).first()
        
        return authorization is not None