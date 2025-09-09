"""
Multi-tenant SaaS Database Models for KanoonPK Legal Research Platform
"""
import os
from datetime import datetime, timedelta
from flask import g
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import func, text
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# =============================================================================
# PUBLIC SCHEMA MODELS (Shared across all tenants)
# =============================================================================

class Tenant(db.Model):
    """Tenant organizations - each gets their own schema"""
    __tablename__ = 'tenants'
    __table_args__ = {'schema': 'public'}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    subdomain = db.Column(db.String(100), unique=True, nullable=False)
    plan = db.Column(db.String(50), default='free')  # free, lawyer, firm, enterprise
    status = db.Column(db.String(50), default='active')  # active, suspended, deleted
    
    # Plan limits
    max_documents = db.Column(db.Integer, default=10)
    max_queries_per_month = db.Column(db.Integer, default=100)
    max_users = db.Column(db.Integer, default=1)
    max_storage_mb = db.Column(db.Integer, default=100)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='tenant_ref', lazy='dynamic')
    subscriptions = db.relationship('Subscription', backref='tenant_ref', lazy='dynamic')
    usage_metrics = db.relationship('UsageMetric', backref='tenant_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tenant {self.name} ({self.subdomain})>'
    
    def get_current_usage(self, metric_type, month_year=None):
        """Get current usage for a specific metric type"""
        if not month_year:
            month_year = datetime.utcnow().strftime('%Y-%m')
        
        usage = UsageMetric.query.filter_by(
            tenant_id=self.id,
            metric_type=metric_type,
            month_year=month_year
        ).first()
        
        return usage.count if usage else 0
    
    def can_perform_action(self, action_type):
        """Check if tenant can perform an action based on their plan limits"""
        current_month = datetime.utcnow().strftime('%Y-%m')
        
        if action_type == 'query':
            current_queries = self.get_current_usage('query', current_month)
            return current_queries < self.max_queries_per_month
        elif action_type == 'document_upload':
            current_docs = self.get_current_usage('document_upload')
            return current_docs < self.max_documents
        elif action_type == 'add_user':
            current_users = self.users.filter_by(status='active').count()
            return current_users < self.max_users
        
        return False
    
    def get_schema_name(self):
        """Get the PostgreSQL schema name for this tenant"""
        return f"tenant_{self.id}"

class User(UserMixin, db.Model):
    """Users belong to tenants"""
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    
    # Tenant relationship
    tenant_id = db.Column(db.Integer, db.ForeignKey('public.tenants.id'), nullable=False)
    
    # User properties
    role = db.Column(db.String(50), default='member')  # owner, admin, member, viewer
    status = db.Column(db.String(50), default='active')  # active, suspended, deleted
    is_verified = db.Column(db.Boolean, default=False)
    
    # Activity tracking
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    usage_metrics = db.relationship('UsageMetric', backref='user_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        role_permissions = {
            'owner': ['all'],
            'admin': ['manage_users', 'manage_documents', 'view_analytics', 'export_data'],
            'member': ['upload_documents', 'search', 'export_own_data'],
            'viewer': ['search', 'view_documents']
        }
        
        user_permissions = role_permissions.get(self.role, [])
        return permission in user_permissions or 'all' in user_permissions

class Subscription(db.Model):
    """Subscription management for tenants"""
    __tablename__ = 'subscriptions'
    __table_args__ = {'schema': 'public'}
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('public.tenants.id'), nullable=False)
    
    # Subscription details
    plan_name = db.Column(db.String(100), nullable=False)  # free, lawyer, firm, enterprise
    status = db.Column(db.String(50), default='active')  # active, canceled, past_due, unpaid
    
    # Billing cycle
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    
    # External payment provider
    stripe_subscription_id = db.Column(db.String(255))
    stripe_customer_id = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subscription {self.plan_name} for Tenant {self.tenant_id}>'
    
    def is_active(self):
        """Check if subscription is currently active"""
        return (self.status == 'active' and 
                self.current_period_end and 
                self.current_period_end > datetime.utcnow())

class UsageMetric(db.Model):
    """Track usage metrics for billing and limits"""
    __tablename__ = 'usage_metrics'
    __table_args__ = {'schema': 'public'}
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('public.tenants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('public.users.id'), nullable=True)
    
    # Metric details
    metric_type = db.Column(db.String(100), nullable=False)  # query, document_upload, api_call, storage_mb
    count = db.Column(db.Integer, default=1)
    metric_data = db.Column(db.JSON)  # Additional metric data
    
    # Time tracking
    month_year = db.Column(db.String(7), nullable=False)  # Format: '2024-12'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UsageMetric {self.metric_type}: {self.count} for Tenant {self.tenant_id}>'

# =============================================================================
# TENANT-SPECIFIC SCHEMA MODELS (Per-tenant isolation)
# =============================================================================

class TenantAwareModel(db.Model):
    """Base class for tenant-specific models"""
    __abstract__ = True
    
    @classmethod
    def get_schema_name(cls):
        """Get current tenant schema from Flask g context"""
        if hasattr(g, 'tenant'):
            return g.tenant.get_schema_name()
        return 'public'  # Fallback to public schema

class LegalDocument(TenantAwareModel):
    """Legal documents uploaded by tenants (stored in tenant-specific schema)"""
    __tablename__ = 'legal_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Document metadata
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    file_path = db.Column(db.String(500))  # Path to stored file
    
    # Legal categorization
    document_type = db.Column(db.String(100))  # case_law, statute, contract, pleading, opinion
    legal_area = db.Column(db.JSON)  # Array of legal practice areas
    jurisdiction = db.Column(db.String(200))  # Pakistan Supreme Court, Lahore High Court, etc.
    court_level = db.Column(db.String(100))  # supreme, high, district, session
    
    # Content analysis
    total_chunks = db.Column(db.Integer, default=0)
    extracted_citations = db.Column(db.JSON)  # Array of legal citations found
    extracted_entities = db.Column(db.JSON)  # Legal entities, parties, etc.
    
    # Metadata
    upload_user_id = db.Column(db.Integer)  # References public.users.id
    processing_status = db.Column(db.String(50), default='pending')  # pending, processed, failed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LegalDocument {self.filename}>'

class QueryHistory(TenantAwareModel):
    """Query history for each tenant"""
    __tablename__ = 'query_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Query details
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    
    # Search metadata
    search_filters = db.Column(db.JSON)  # Applied filters
    found_citations = db.Column(db.JSON)  # Citations in response
    confidence_score = db.Column(db.Float)
    
    # User context
    user_id = db.Column(db.Integer)  # References public.users.id
    session_id = db.Column(db.String(100))
    
    # Performance metrics
    response_time_ms = db.Column(db.Integer)
    tokens_used = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<QueryHistory {self.question[:50]}...>'

class LegalWorkspace(TenantAwareModel):
    """Collaborative workspaces for legal research"""
    __tablename__ = 'legal_workspaces'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Workspace details
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Access control
    owner_user_id = db.Column(db.Integer, nullable=False)  # References public.users.id
    shared_with = db.Column(db.JSON)  # Array of user IDs with access
    is_public = db.Column(db.Boolean, default=False)
    
    # Content
    saved_queries = db.Column(db.JSON)  # Array of saved query objects
    bookmarked_documents = db.Column(db.JSON)  # Array of document IDs
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LegalWorkspace {self.name}>'

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_tenant_schema(tenant_id):
    """Create a new schema for a tenant and all necessary tables"""
    schema_name = f"tenant_{tenant_id}"
    
    try:
        # Create schema
        db.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        
        # Set search path to include new schema
        db.session.execute(text(f'SET search_path TO "{schema_name}", public'))
        
        # Create tenant-specific tables
        tenant_tables = [LegalDocument, QueryHistory, LegalWorkspace]
        
        for table_class in tenant_tables:
            table = table_class.__table__
            table.schema = schema_name
            table.create(db.engine, checkfirst=True)
        
        db.session.commit()
        print(f"Created schema '{schema_name}' with tables")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating tenant schema: {e}")
        return False

def switch_tenant_schema(tenant_id):
    """Switch to a tenant's schema for subsequent queries"""
    if tenant_id:
        schema_name = f"tenant_{tenant_id}"
        db.session.execute(text(f'SET search_path TO "{schema_name}", public'))

def get_tenant_from_subdomain(subdomain):
    """Get tenant by subdomain"""
    return Tenant.query.filter_by(subdomain=subdomain, status='active').first()

def record_usage(tenant_id, user_id, metric_type, count=1, metadata=None):
    """Record usage metric for billing/limits tracking"""
    month_year = datetime.utcnow().strftime('%Y-%m')
    
    # Check if metric already exists for this month
    existing_metric = UsageMetric.query.filter_by(
        tenant_id=tenant_id,
        user_id=user_id,
        metric_type=metric_type,
        month_year=month_year
    ).first()
    
    if existing_metric:
        existing_metric.count += count
        if metadata:
            existing_metric.metric_data = metadata
    else:
        new_metric = UsageMetric(
            tenant_id=tenant_id,
            user_id=user_id,
            metric_type=metric_type,
            count=count,
            month_year=month_year,
            metric_data=metadata
        )
        db.session.add(new_metric)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error recording usage metric: {e}")

# =============================================================================
# PLAN DEFINITIONS
# =============================================================================

PLAN_LIMITS = {
    'free': {
        'max_documents': 10,
        'max_queries_per_month': 100,
        'max_users': 1,
        'max_storage_mb': 100,
        'features': ['basic_search', 'document_upload', 'pdf_export']
    },
    'lawyer': {
        'max_documents': 100,
        'max_queries_per_month': 1000,
        'max_users': 3,
        'max_storage_mb': 1000,
        'features': ['advanced_search', 'citation_analysis', 'precedent_matching', 'workspace_collaboration']
    },
    'firm': {
        'max_documents': 500,
        'max_queries_per_month': 5000,
        'max_users': 15,
        'max_storage_mb': 10000,
        'features': ['all_lawyer_features', 'team_analytics', 'custom_exports', 'api_access']
    },
    'enterprise': {
        'max_documents': -1,  # Unlimited
        'max_queries_per_month': -1,  # Unlimited
        'max_users': -1,  # Unlimited
        'max_storage_mb': -1,  # Unlimited
        'features': ['all_features', 'priority_support', 'custom_integrations', 'sso']
    }
}