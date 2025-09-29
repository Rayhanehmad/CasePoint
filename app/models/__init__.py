"""
Modern database models with enhanced multi-tenancy
"""
from app.models.base import BaseModel
from app.models.tenant import Tenant, TenantUser
from app.models.user import User, UserRole, Permission
from app.models.subscription import Subscription, Plan, Feature
from app.models.legal import LegalDocument, SearchQuery, Citation
from app.models.analytics import AnalyticsEvent, UsageMetric

__all__ = [
    'BaseModel',
    'Tenant', 'TenantUser',
    'User', 'UserRole', 'Permission', 
    'Subscription', 'Plan', 'Feature',
    'LegalDocument', 'SearchQuery', 'Citation',
    'AnalyticsEvent', 'UsageMetric'
]