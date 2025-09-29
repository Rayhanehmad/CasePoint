"""
Initialize default data for the application
"""
import logging
from app import db
from app.models.subscription import Plan, PlanType, Feature

logger = logging.getLogger(__name__)

def initialize_default_data():
    """Initialize default plans, features, and system data"""
    
    try:
        # Check if plans already exist
        if Plan.query.first():
            logger.info("Default data already exists, skipping initialization")
            return
        
        logger.info("Initializing default data...")
        
        # Create default plans
        create_default_plans()
        
        # Create default features
        create_default_features()
        
        # Commit all changes
        db.session.commit()
        
        logger.info("Default data initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error initializing default data: {e}")
        db.session.rollback()

def create_default_plans():
    """Create default subscription plans"""
    
    default_plans = Plan.get_default_plans()
    
    for plan_type, plan_data in default_plans.items():
        plan = Plan(
            name=plan_data['name'],
            plan_type=plan_type,
            description=f"{plan_data['name']} plan for legal professionals",
            monthly_price=plan_data['monthly_price'],
            yearly_price=plan_data['yearly_price'],
            limits=plan_data['limits'],
            features=plan_data['features'],
            is_active=True,
            display_order=list(default_plans.keys()).index(plan_type)
        )
        
        if plan_type == PlanType.LAWYER:
            plan.is_featured = True
        
        db.session.add(plan)
        logger.info(f"Created plan: {plan.name}")

def create_default_features():
    """Create default feature definitions"""
    
    features = [
        # Search features
        {
            'name': 'basic_search',
            'display_name': 'Basic Search',
            'description': 'Basic keyword search through legal documents',
            'category': 'search',
            'is_premium': False
        },
        {
            'name': 'advanced_search',
            'display_name': 'Advanced Search',
            'description': 'Advanced search with filters and boolean operators',
            'category': 'search',
            'is_premium': True
        },
        {
            'name': 'ai_search',
            'display_name': 'AI-Powered Search',
            'description': 'Intelligent search using AI to understand context and intent',
            'category': 'search',
            'is_premium': True
        },
        {
            'name': 'citation_search',
            'display_name': 'Citation Search',
            'description': 'Search for specific legal citations (PLD, SCMR, CLR, MLD)',
            'category': 'search',
            'is_premium': False
        },
        {
            'name': 'precedent_analysis',
            'display_name': 'Precedent Analysis',
            'description': 'AI-powered analysis of legal precedents and similar cases',
            'category': 'search',
            'is_premium': True
        },
        
        # Document features
        {
            'name': 'document_upload',
            'display_name': 'Document Upload',
            'description': 'Upload and process legal documents (PDF, DOCX, TXT)',
            'category': 'document',
            'is_premium': False
        },
        {
            'name': 'document_analysis',
            'display_name': 'Document Analysis',
            'description': 'Automatic analysis and categorization of legal documents',
            'category': 'document',
            'is_premium': True
        },
        {
            'name': 'export_results',
            'display_name': 'Export Results',
            'description': 'Export search results and documents to PDF, DOCX, CSV',
            'category': 'document',
            'is_premium': True
        },
        
        # Collaboration features
        {
            'name': 'team_collaboration',
            'display_name': 'Team Collaboration',
            'description': 'Collaborate with team members on legal research',
            'category': 'collaboration',
            'is_premium': True
        },
        {
            'name': 'shared_workspaces',
            'display_name': 'Shared Workspaces',
            'description': 'Create and manage shared research workspaces',
            'category': 'collaboration',
            'is_premium': True
        },
        
        # Analytics features
        {
            'name': 'analytics_dashboard',
            'display_name': 'Analytics Dashboard',
            'description': 'Comprehensive analytics and usage insights',
            'category': 'analytics',
            'is_premium': True
        },
        {
            'name': 'usage_reports',
            'display_name': 'Usage Reports',
            'description': 'Detailed reports on search patterns and usage',
            'category': 'analytics',
            'is_premium': True
        },
        
        # Integration features
        {
            'name': 'api_access',
            'display_name': 'API Access',
            'description': 'REST API access for custom integrations',
            'category': 'integration',
            'is_premium': True
        },
        {
            'name': 'webhook_notifications',
            'display_name': 'Webhook Notifications',
            'description': 'Real-time notifications via webhooks',
            'category': 'integration',
            'is_premium': True
        },
        
        # Enterprise features
        {
            'name': 'sso_integration',
            'display_name': 'SSO Integration',
            'description': 'Single Sign-On integration with enterprise systems',
            'category': 'enterprise',
            'is_premium': True,
            'requires_setup': True
        },
        {
            'name': 'custom_domain',
            'display_name': 'Custom Domain',
            'description': 'Use your own custom domain for the platform',
            'category': 'enterprise',
            'is_premium': True,
            'requires_setup': True
        },
        {
            'name': 'white_label',
            'display_name': 'White Label',
            'description': 'Customize branding and appearance',
            'category': 'enterprise',
            'is_premium': True,
            'requires_setup': True
        },
        {
            'name': 'dedicated_support',
            'display_name': 'Dedicated Support',
            'description': 'Priority support with dedicated account manager',
            'category': 'enterprise',
            'is_premium': True
        }
    ]
    
    for feature_data in features:
        feature = Feature(**feature_data)
        db.session.add(feature)
        logger.info(f"Created feature: {feature.display_name}")