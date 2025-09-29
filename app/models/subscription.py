"""
Subscription and billing models
"""
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal as PyDecimal
from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import UUID, JSON
from app import db
from app.models.base import BaseModel

class PlanType(Enum):
    FREE = "free"
    LAWYER = "lawyer"
    FIRM = "firm"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    PAUSED = "paused"

class BillingInterval(Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Plan(BaseModel):
    """Subscription plans with features and limits"""
    
    # Basic information
    name = db.Column(db.String(50), nullable=False)
    plan_type = db.Column(db.Enum(PlanType), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    
    # Pricing
    monthly_price = db.Column(Numeric(10, 2), nullable=False, default=0)
    yearly_price = db.Column(Numeric(10, 2), nullable=False, default=0)
    
    # Stripe integration
    stripe_monthly_price_id = db.Column(db.String(100), nullable=True)
    stripe_yearly_price_id = db.Column(db.String(100), nullable=True)
    
    # Limits and features
    limits = db.Column(JSON, nullable=False, default=dict)
    features = db.Column(JSON, nullable=False, default=list)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    
    # Display
    display_order = db.Column(db.Integer, default=0)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='plan', lazy='dynamic')
    
    def __repr__(self):
        return f'<Plan {self.name}>'
    
    @classmethod
    def get_default_plans(cls):
        """Get default plan configurations"""
        return {
            PlanType.FREE: {
                'name': 'Free',
                'monthly_price': 0,
                'yearly_price': 0,
                'limits': {
                    'max_users': 1,
                    'max_documents': 10,
                    'max_storage_mb': 100,
                    'max_monthly_searches': 50,
                    'max_ai_queries': 10
                },
                'features': ['basic_search', 'document_upload', 'citation_search']
            },
            PlanType.LAWYER: {
                'name': 'Individual Lawyer',
                'monthly_price': 29.99,
                'yearly_price': 299.99,
                'limits': {
                    'max_users': 1,
                    'max_documents': 500,
                    'max_storage_mb': 5000,
                    'max_monthly_searches': 1000,
                    'max_ai_queries': 100
                },
                'features': ['advanced_search', 'ai_search', 'document_upload', 
                            'citation_search', 'precedent_analysis', 'export_results']
            },
            PlanType.FIRM: {
                'name': 'Law Firm',
                'monthly_price': 99.99,
                'yearly_price': 999.99,
                'limits': {
                    'max_users': 25,
                    'max_documents': 5000,
                    'max_storage_mb': 50000,
                    'max_monthly_searches': 10000,
                    'max_ai_queries': 1000
                },
                'features': ['advanced_search', 'ai_search', 'document_upload',
                            'citation_search', 'precedent_analysis', 'export_results',
                            'team_collaboration', 'analytics_dashboard', 'api_access']
            },
            PlanType.ENTERPRISE: {
                'name': 'Enterprise',
                'monthly_price': 299.99,
                'yearly_price': 2999.99,
                'limits': {
                    'max_users': -1,  # Unlimited
                    'max_documents': -1,
                    'max_storage_mb': -1,
                    'max_monthly_searches': -1,
                    'max_ai_queries': -1
                },
                'features': ['all_features', 'custom_integrations', 'dedicated_support',
                            'white_label', 'custom_domain', 'sso_integration']
            }
        }
    
    def get_price_for_interval(self, interval):
        """Get price for billing interval"""
        if interval == BillingInterval.YEARLY:
            return self.yearly_price
        return self.monthly_price
    
    def has_feature(self, feature_name):
        """Check if plan includes specific feature"""
        return feature_name in self.features or 'all_features' in self.features
    
    def is_limit_exceeded(self, metric, current_value):
        """Check if current usage exceeds plan limit"""
        limit = self.limits.get(metric, 0)
        if limit == -1:  # Unlimited
            return False
        return current_value >= limit

class Subscription(BaseModel):
    """User subscriptions with Stripe integration"""
    
    # Tenant relationship
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenant.id'), nullable=False)
    plan_id = db.Column(UUID(as_uuid=True), db.ForeignKey('plan.id'), nullable=False)
    
    # Stripe integration
    stripe_subscription_id = db.Column(db.String(100), unique=True, nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    
    # Subscription details
    status = db.Column(db.Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIALING)
    billing_interval = db.Column(db.Enum(BillingInterval), nullable=False, default=BillingInterval.MONTHLY)
    
    # Dates
    trial_start = db.Column(db.DateTime, nullable=True)
    trial_end = db.Column(db.DateTime, nullable=True)
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    
    # Pricing
    current_price = db.Column(Numeric(10, 2), nullable=False, default=0)
    
    # Usage tracking
    usage_data = db.Column(JSON, default=dict)
    
    def __repr__(self):
        return f'<Subscription {self.tenant_id}:{self.plan.name}>'
    
    @property
    def is_active(self):
        """Check if subscription is active"""
        return self.status == SubscriptionStatus.ACTIVE
    
    @property
    def is_trial(self):
        """Check if subscription is in trial"""
        return self.status == SubscriptionStatus.TRIALING
    
    @property
    def trial_days_remaining(self):
        """Get remaining trial days"""
        if not self.trial_end:
            return 0
        delta = self.trial_end - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def days_until_renewal(self):
        """Get days until next renewal"""
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)
    
    def start_trial(self, trial_days=14):
        """Start trial period"""
        self.status = SubscriptionStatus.TRIALING
        self.trial_start = datetime.utcnow()
        self.trial_end = datetime.utcnow() + timedelta(days=trial_days)
    
    def activate_subscription(self):
        """Activate paid subscription"""
        self.status = SubscriptionStatus.ACTIVE
        if not self.current_period_start:
            self.current_period_start = datetime.utcnow()
        
        # Set next billing date
        if self.billing_interval == BillingInterval.YEARLY:
            self.current_period_end = self.current_period_start + timedelta(days=365)
        else:
            self.current_period_end = self.current_period_start + timedelta(days=30)
    
    def cancel_subscription(self, at_period_end=True):
        """Cancel subscription"""
        self.cancelled_at = datetime.utcnow()
        if not at_period_end:
            self.status = SubscriptionStatus.CANCELLED
            self.ended_at = datetime.utcnow()
    
    def update_usage(self, metric, value):
        """Update usage metric"""
        if not self.usage_data:
            self.usage_data = {}
        self.usage_data[metric] = value
        self.save()
    
    def get_usage(self, metric):
        """Get current usage for metric"""
        return self.usage_data.get(metric, 0) if self.usage_data else 0

class Feature(BaseModel):
    """Individual features that can be included in plans"""
    
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # e.g., 'search', 'analytics', 'integration'
    
    # Feature configuration
    is_premium = db.Column(db.Boolean, default=False)
    requires_setup = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Feature {self.name}>'