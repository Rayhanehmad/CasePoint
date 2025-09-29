"""
Analytics and usage tracking models
"""
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID, JSON
from app import db
from app.models.base import BaseModel, TenantMixin

class EventType(Enum):
    # User events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_SIGNUP = "user_signup"
    
    # Search events
    SEARCH_PERFORMED = "search_performed"
    SEARCH_RESULT_CLICKED = "search_result_clicked"
    AI_QUERY_EXECUTED = "ai_query_executed"
    CITATION_SEARCH = "citation_search"
    
    # Document events
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_VIEWED = "document_viewed"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    DOCUMENT_SHARED = "document_shared"
    
    # Subscription events
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    TRIAL_STARTED = "trial_started"
    TRIAL_ENDED = "trial_ended"
    
    # Feature usage
    FEATURE_USED = "feature_used"
    API_CALL = "api_call"
    EXPORT_PERFORMED = "export_performed"

class AnalyticsEvent(BaseModel, TenantMixin):
    """Individual analytics events with detailed tracking"""
    
    # Event identification
    event_type = db.Column(db.Enum(EventType), nullable=False, index=True)
    event_name = db.Column(db.String(100), nullable=False)
    
    # User and session
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)
    
    # Event data
    properties = db.Column(JSON, default=dict)
    event_metadata = db.Column(JSON, default=dict)
    
    # Context
    page_url = db.Column(db.String(500), nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Geography (if available)
    country = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(50), nullable=True)
    
    # Performance
    processing_time_ms = db.Column(db.Integer, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='analytics_events')
    
    def __repr__(self):
        return f'<AnalyticsEvent {self.event_type.value}>'
    
    @classmethod
    def track_event(cls, event_type, event_name, user_id=None, tenant_id=None, **kwargs):
        """Track an analytics event"""
        from flask import request, g
        
        # Get tenant from context if not provided
        if not tenant_id and hasattr(g, 'tenant'):
            tenant_id = g.tenant.id
        
        # Get user from context if not provided
        if not user_id and hasattr(g, 'current_user') and g.current_user:
            user_id = g.current_user.id
        
        event = cls(
            event_type=event_type,
            event_name=event_name,
            user_id=user_id,
            tenant_id=tenant_id,
            properties=kwargs.get('properties', {}),
            event_metadata=kwargs.get('metadata', {}),
            page_url=request.url if request else None,
            referrer=request.referrer if request else None,
            user_agent=request.headers.get('User-Agent') if request else None,
            ip_address=request.environ.get('REMOTE_ADDR') if request else None,
            session_id=kwargs.get('session_id'),
            processing_time_ms=kwargs.get('processing_time_ms')
        )
        
        event.save()
        return event

class UsageMetric(BaseModel, TenantMixin):
    """Aggregated usage metrics for reporting and billing"""
    
    # Metric identification
    metric_name = db.Column(db.String(50), nullable=False, index=True)
    metric_category = db.Column(db.String(50), nullable=False)  # search, document, user, api
    
    # Time period
    period_type = db.Column(db.String(20), nullable=False)  # hourly, daily, weekly, monthly
    period_start = db.Column(db.DateTime, nullable=False, index=True)
    period_end = db.Column(db.DateTime, nullable=False)
    
    # Values
    count_value = db.Column(db.Integer, default=0)
    sum_value = db.Column(db.Float, default=0.0)
    avg_value = db.Column(db.Float, default=0.0)
    max_value = db.Column(db.Float, default=0.0)
    min_value = db.Column(db.Float, default=0.0)
    
    # Dimensions
    dimensions = db.Column(JSON, default=dict)  # Additional grouping dimensions
    
    # Unique constraint for metric aggregation
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'metric_name', 'period_type', 'period_start', 
                          name='unique_usage_metric'),
    )
    
    def __repr__(self):
        return f'<UsageMetric {self.metric_name}:{self.period_type}>'
    
    @classmethod
    def record_usage(cls, tenant_id, metric_name, value=1, category='general', **dimensions):
        """Record usage metric for current period"""
        
        # Determine period boundaries
        now = datetime.utcnow()
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)  # Daily aggregation
        period_end = period_start + timedelta(days=1)
        
        # Find or create metric record
        metric = cls.query.filter_by(
            tenant_id=tenant_id,
            metric_name=metric_name,
            period_type='daily',
            period_start=period_start
        ).first()
        
        if not metric:
            metric = cls(
                tenant_id=tenant_id,
                metric_name=metric_name,
                metric_category=category,
                period_type='daily',
                period_start=period_start,
                period_end=period_end,
                dimensions=dimensions
            )
        
        # Update values
        metric.count_value += 1
        metric.sum_value += value
        metric.avg_value = metric.sum_value / metric.count_value
        
        if value > metric.max_value:
            metric.max_value = value
        if metric.min_value == 0 or value < metric.min_value:
            metric.min_value = value
        
        metric.save()
        return metric
    
    @classmethod
    def get_usage_summary(cls, tenant_id, metric_names=None, days=30):
        """Get usage summary for tenant"""
        query = cls.query.filter(
            cls.tenant_id == tenant_id,
            cls.period_start >= datetime.utcnow() - timedelta(days=days)
        )
        
        if metric_names:
            query = query.filter(cls.metric_name.in_(metric_names))
        
        metrics = query.all()
        
        summary = {}
        for metric in metrics:
            if metric.metric_name not in summary:
                summary[metric.metric_name] = {
                    'total_count': 0,
                    'total_sum': 0,
                    'avg_daily': 0,
                    'peak_day': 0,
                    'category': metric.metric_category
                }
            
            summary[metric.metric_name]['total_count'] += metric.count_value
            summary[metric.metric_name]['total_sum'] += metric.sum_value
            if metric.count_value > summary[metric.metric_name]['peak_day']:
                summary[metric.metric_name]['peak_day'] = metric.count_value
        
        # Calculate averages
        for metric_name in summary:
            total_count = summary[metric_name]['total_count']
            summary[metric_name]['avg_daily'] = total_count / days if days > 0 else 0
        
        return summary

class DashboardWidget(BaseModel, TenantMixin):
    """Customizable dashboard widgets for analytics"""
    
    # Widget identification
    widget_type = db.Column(db.String(50), nullable=False)  # chart, metric, table
    widget_name = db.Column(db.String(100), nullable=False)
    
    # Configuration
    config = db.Column(JSON, nullable=False, default=dict)
    query_config = db.Column(JSON, nullable=False, default=dict)
    
    # Layout
    position_x = db.Column(db.Integer, default=0)
    position_y = db.Column(db.Integer, default=0)
    width = db.Column(db.Integer, default=1)
    height = db.Column(db.Integer, default=1)
    
    # Access
    is_public = db.Column(db.Boolean, default=False)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='created_widgets')
    
    def __repr__(self):
        return f'<DashboardWidget {self.widget_name}>'
    
    def get_data(self):
        """Execute widget query and return data"""
        # This would implement the actual data fetching logic
        # based on the query_config
        pass

class ReportTemplate(BaseModel, TenantMixin):
    """Report templates for analytics and business intelligence"""
    
    # Template details
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    report_type = db.Column(db.String(50), nullable=False)  # usage, billing, legal_analytics
    
    # Configuration
    config = db.Column(JSON, nullable=False, default=dict)
    schedule_config = db.Column(JSON, default=dict)  # For automated reports
    
    # Template content
    template_content = db.Column(db.Text, nullable=True)  # HTML/JSON template
    
    # Access and sharing
    is_system_template = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='report_templates')
    
    def __repr__(self):
        return f'<ReportTemplate {self.name}>'