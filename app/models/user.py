"""
User authentication and authorization models
"""
import secrets
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID, JSON
from app import db
from app.models.base import BaseModel

class User(UserMixin, BaseModel):
    """Enhanced user model with modern features"""
    
    # Basic information
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    
    # Authentication
    password_hash = db.Column(db.String(256), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(100), nullable=True)
    
    # Password reset
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    
    # Profile
    avatar_url = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(5), default='en')
    
    # Professional information
    organization = db.Column(db.String(100), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    bar_license = db.Column(db.String(50), nullable=True)
    practice_areas = db.Column(JSON, default=list)
    
    # Settings and preferences
    preferences = db.Column(JSON, default=dict)
    notification_settings = db.Column(JSON, default=dict)
    
    # Security
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(100), nullable=True)
    
    # Relationships
    tenant_associations = db.relationship('TenantUser', backref='user', lazy='dynamic')
    search_queries = db.relationship('SearchQuery', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.email.split('@')[0]
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def generate_email_verification_token(self):
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token
    
    def verify_email(self, token):
        """Verify email with token"""
        if self.email_verification_token == token:
            self.email_verified = True
            self.email_verification_token = None
            return True
        return False
    
    def generate_password_reset_token(self):
        """Generate password reset token"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token
    
    def reset_password(self, token, new_password):
        """Reset password with token"""
        if (self.password_reset_token == token and 
            self.password_reset_expires and 
            datetime.utcnow() < self.password_reset_expires):
            
            self.set_password(new_password)
            self.password_reset_token = None
            self.password_reset_expires = None
            return True
        return False
    
    def record_login(self):
        """Record user login"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
    
    def get_tenant_role(self, tenant_id):
        """Get user's role in specific tenant"""
        tenant_user = self.tenant_associations.filter_by(tenant_id=tenant_id).first()
        return tenant_user.role if tenant_user else None
    
    def is_tenant_member(self, tenant_id):
        """Check if user is member of tenant"""
        return self.tenant_associations.filter_by(
            tenant_id=tenant_id, 
            is_active=True
        ).first() is not None
    
    def get_active_tenants(self):
        """Get all active tenants for user"""
        return [tu.tenant for tu in self.tenant_associations.filter_by(is_active=True)]
    
    def update_preferences(self, **kwargs):
        """Update user preferences"""
        if not self.preferences:
            self.preferences = {}
        self.preferences.update(kwargs)
        self.save()

class UserRole(BaseModel):
    """User roles for RBAC system"""
    
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Permissions
    permissions = db.relationship('Permission', secondary='role_permissions', backref='roles')
    
    def __repr__(self):
        return f'<UserRole {self.name}>'
    
    def has_permission(self, permission_name):
        """Check if role has specific permission"""
        return any(p.name == permission_name for p in self.permissions)

class Permission(BaseModel):
    """Permissions for RBAC system"""
    
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    resource = db.Column(db.String(50), nullable=False)  # e.g., 'document', 'search'
    action = db.Column(db.String(50), nullable=False)    # e.g., 'read', 'write', 'delete'
    
    def __repr__(self):
        return f'<Permission {self.name}>'

# Association table for role-permission many-to-many relationship
role_permissions = db.Table('role_permissions',
    db.Column('role_id', UUID(as_uuid=True), db.ForeignKey('user_role.id'), primary_key=True),
    db.Column('permission_id', UUID(as_uuid=True), db.ForeignKey('permission.id'), primary_key=True)
)