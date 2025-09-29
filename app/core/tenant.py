"""
Modern Multi-Tenant Management System
Enhanced tenant isolation and context management
"""
import logging
from flask import g, request, session, current_app
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class TenantManager:
    """Modern tenant management with enhanced features"""
    
    @staticmethod
    def load_tenant_context():
        """
        Load tenant context from various sources:
        1. Subdomain (tenant.kanoonpk.com)
        2. Custom domain mapping
        3. API header (X-Tenant-ID)
        4. Session (for development)
        """
        tenant = None
        tenant_source = None
        
        # Skip tenant loading for public routes
        if TenantManager._is_public_route():
            return
        
        # Method 1: Extract from subdomain
        tenant_subdomain = TenantManager._extract_subdomain()
        if tenant_subdomain:
            tenant = TenantManager._get_tenant_by_subdomain(tenant_subdomain)
            tenant_source = 'subdomain'
        
        # Method 2: Check API header
        if not tenant and request.headers.get('X-Tenant-ID'):
            tenant_id = request.headers.get('X-Tenant-ID')
            tenant = TenantManager._get_tenant_by_id(tenant_id)
            tenant_source = 'header'
        
        # Method 3: Check custom domain
        if not tenant:
            tenant = TenantManager._get_tenant_by_domain(request.host)
            tenant_source = 'domain'
        
        # Method 4: Development fallback
        if not tenant and current_app.config.get('DEVELOPMENT'):
            tenant_subdomain = request.args.get('tenant') or session.get('tenant_subdomain')
            if tenant_subdomain:
                tenant = TenantManager._get_tenant_by_subdomain(tenant_subdomain)
                tenant_source = 'development'
        
        # Set tenant context
        if tenant:
            g.tenant = tenant
            g.tenant_source = tenant_source
            session['tenant_subdomain'] = tenant.subdomain
            
            # Switch database schema if needed
            TenantManager._switch_tenant_schema(tenant.id)
            
            logger.debug(f"Loaded tenant: {tenant.name} (source: {tenant_source})")
        else:
            # No tenant found for protected route
            if not TenantManager._is_public_route():
                logger.warning(f"No tenant context for route: {request.path}")
    
    @staticmethod
    def _is_public_route():
        """Check if current route is public (doesn't require tenant)"""
        public_routes = [
            '/', '/health', '/ping',
            '/auth/login', '/auth/register', '/auth/signup',
            '/auth/forgot-password', '/auth/reset-password',
            '/api/v1/public', '/api/v1/health',
        ]
        
        public_prefixes = [
            '/static/', '/favicon.ico', 
            '/auth/public/', '/api/v1/public/'
        ]
        
        # Check exact matches
        if request.path in public_routes:
            return True
        
        # Check prefix matches
        for prefix in public_prefixes:
            if request.path.startswith(prefix):
                return True
        
        # Check endpoint names
        public_endpoints = [
            'main.public_home', 'main.pricing', 'main.features',
            'auth.login', 'auth.register', 'auth.signup',
            'api.public_features', 'static'
        ]
        
        if request.endpoint in public_endpoints:
            return True
        
        return False
    
    @staticmethod
    def _extract_subdomain():
        """Extract subdomain from request host"""
        host = request.host.lower()
        
        # Handle localhost and development
        if any(dev_host in host for dev_host in ['localhost', '127.0.0.1', '0.0.0.0']):
            return None
        
        # Extract subdomain
        parts = host.split('.')
        if len(parts) >= 3:
            subdomain = parts[0]
            # Exclude common prefixes
            if subdomain not in ['www', 'api', 'admin', 'app']:
                return subdomain
        
        return None
    
    @staticmethod
    def _get_tenant_by_subdomain(subdomain):
        """Get tenant by subdomain"""
        try:
            from app.models import Tenant
            return Tenant.query.filter_by(
                subdomain=subdomain, 
                is_active=True
            ).first()
        except Exception as e:
            logger.error(f"Error fetching tenant by subdomain: {e}")
            return None
    
    @staticmethod
    def _get_tenant_by_id(tenant_id):
        """Get tenant by ID"""
        try:
            from app.models import Tenant
            return Tenant.query.filter_by(
                id=tenant_id, 
                is_active=True
            ).first()
        except Exception as e:
            logger.error(f"Error fetching tenant by ID: {e}")
            return None
    
    @staticmethod
    def _get_tenant_by_domain(domain):
        """Get tenant by custom domain"""
        try:
            from app.models import Tenant
            return Tenant.query.filter_by(
                custom_domain=domain, 
                is_active=True
            ).first()
        except Exception as e:
            logger.error(f"Error fetching tenant by domain: {e}")
            return None
    
    @staticmethod
    def _switch_tenant_schema(tenant_id):
        """Switch database schema for tenant isolation"""
        try:
            from app import db
            # For PostgreSQL: SET search_path TO tenant_schema
            schema_name = f"tenant_{tenant_id}"
            db.session.execute(f"SET search_path TO {schema_name}, public")
            g.tenant_schema = schema_name
        except Exception as e:
            logger.error(f"Error switching tenant schema: {e}")
    
    @staticmethod
    def get_current_tenant():
        """Get current tenant from context"""
        return getattr(g, 'tenant', None)
    
    @staticmethod
    def require_tenant():
        """Decorator to require tenant context"""
        def decorator(f):
            from functools import wraps
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(g, 'tenant'):
                    from flask import jsonify, abort
                    if request.path.startswith('/api/'):
                        return jsonify({'error': 'Tenant context required'}), 400
                    abort(400)
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def create_tenant_schema(tenant_id):
        """Create isolated schema for new tenant"""
        try:
            from app import db
            schema_name = f"tenant_{tenant_id}"
            
            # Create schema
            db.session.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            
            # Set search path and create tables
            db.session.execute(f"SET search_path TO {schema_name}")
            db.create_all()
            
            # Reset search path
            db.session.execute("SET search_path TO public")
            db.session.commit()
            
            logger.info(f"Created schema for tenant: {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tenant schema: {e}")
            db.session.rollback()
            return False

class TenantContext:
    """Context manager for tenant operations"""
    
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.original_schema = None
    
    def __enter__(self):
        try:
            from app import db
            # Store original schema
            result = db.session.execute("SHOW search_path")
            self.original_schema = result.fetchone()[0]
            
            # Switch to tenant schema
            schema_name = f"tenant_{self.tenant_id}"
            db.session.execute(f"SET search_path TO {schema_name}, public")
            
            return self
        except Exception as e:
            logger.error(f"Error entering tenant context: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            from app import db
            # Restore original schema
            if self.original_schema:
                db.session.execute(f"SET search_path TO {self.original_schema}")
        except Exception as e:
            logger.error(f"Error exiting tenant context: {e}")