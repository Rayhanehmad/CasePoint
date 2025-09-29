"""
Modern Multi-Tenant Management System
Enhanced tenant isolation and context management with bulletproof connection pooling
"""
import logging
import contextvars
from flask import g, request, session, current_app
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Context variable for tenant schema across connection pool
_tenant_schema_context = contextvars.ContextVar('tenant_schema', default='public')

def setup_bulletproof_tenant_isolation(app):
    """Setup bulletproof multi-tenant isolation with connection pooling protection"""
    
    def configure_events():
        """Configure SQLAlchemy events after database initialization"""
        from sqlalchemy import event
        from app import db
        
        # Only set up events once
        if hasattr(app, '_tenant_events_configured'):
            return
        
        @event.listens_for(db.engine, "checkout")
        def set_tenant_schema_on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Ensure every connection checkout has the correct tenant schema (FAIL-CLOSED)"""
            try:
                # Validate PostgreSQL backend
                if not hasattr(dbapi_connection, 'cursor'):
                    app.logger.error("CRITICAL: Non-PostgreSQL connection - tenant isolation requires PostgreSQL")
                    # Should cause the request to fail rather than proceeding unsafely
                    raise Exception("PostgreSQL required for tenant isolation")
                
                schema = _tenant_schema_context.get('public')
                # Use quoted identifier for security
                with dbapi_connection.cursor() as cursor:
                    cursor.execute(f'SET search_path = "{schema}", public')
                    
            except Exception as e:
                # FAIL CLOSED: This is critical for tenant isolation
                app.logger.error(f"CRITICAL: Failed to set tenant schema on checkout: {e}")
                # Raise exception to prevent unsafe database access
                raise Exception(f"Tenant isolation checkout failure: {e}")
        
        @event.listens_for(db.engine, "checkin")  
        def reset_schema_on_checkin(dbapi_connection, connection_record):
            """Reset schema to public when connection returns to pool"""
            try:
                if hasattr(dbapi_connection, 'cursor'):
                    with dbapi_connection.cursor() as cursor:
                        cursor.execute("SET search_path = public")
            except Exception as e:
                # Log but don't fail - this is pool management
                app.logger.error(f"Failed to reset schema on checkin: {e}")
        
        app._tenant_events_configured = True
        app.logger.info("Bulletproof multi-tenant isolation configured")
    
    # Configure events when app context is available
    with app.app_context():
        configure_events()

class TenantManager:
    """Modern tenant management with bulletproof isolation"""
    
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
        
        # Method 2: Check API header (REQUIRES AUTHENTICATION)
        if not tenant and request.headers.get('X-Tenant-ID'):
            from flask_login import current_user
            
            # SECURITY: Only honor X-Tenant-ID for authenticated users
            if current_user and current_user.is_authenticated:
                tenant_id = request.headers.get('X-Tenant-ID')
                tenant = TenantManager._get_tenant_by_id(tenant_id)
                # Validate user has access to this tenant
                if tenant and TenantManager._validate_user_tenant_access(tenant):
                    tenant_source = 'header'
                else:
                    logger.warning(f"Unauthorized tenant access attempt by user {current_user.id}: {tenant_id}")
                    tenant = None
            else:
                logger.warning(f"Unauthenticated X-Tenant-ID header ignored: {request.headers.get('X-Tenant-ID')}")
        
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
            # FAIL CLOSED: No tenant found for protected route
            if not TenantManager._is_public_route():
                logger.error(f"CRITICAL: No tenant context for protected route: {request.path}")
                from flask import abort
                abort(403, "Tenant context required for this resource")
    
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
        """Switch database schema with FAIL-CLOSED protection (no fallback to public)"""
        try:
            from app import db
            from flask import current_app, abort
            from sqlalchemy import text
            
            # Convert UUID to safe schema name  
            safe_tenant_id = str(tenant_id).replace('-', '_')
            schema_name = f"tenant_{safe_tenant_id}"
            
            # CRITICAL: Ensure tenant schema AND tables exist (idempotent)
            success = TenantManager._ensure_tenant_schema_and_tables(tenant_id, schema_name)
            if not success:
                logger.error(f"CRITICAL: Failed to ensure tenant schema {schema_name}")
                abort(503, "Tenant isolation failure - service unavailable")
            
            # Store schema in both Flask context and ContextVar for connection events
            g.tenant_schema = schema_name
            _tenant_schema_context.set(schema_name)
            
            # IMMEDIATELY set search path for current session with quoted identifiers
            try:
                db.session.execute(text(f'SET search_path = "{schema_name}", public'))
                db.session.commit()
                
                # VERIFY search_path was actually set (runtime validation)
                result = db.session.execute(text("SHOW search_path")).fetchone()
                if result and schema_name not in result[0]:
                    logger.error(f"CRITICAL: search_path verification failed for {schema_name}")
                    abort(503, "Tenant isolation verification failed")
                    
            except Exception as e:
                logger.error(f"CRITICAL: Failed to set search_path to {schema_name}: {e}")
                abort(503, "Tenant isolation failure - service unavailable")
            
            current_app.logger.debug(f"Tenant schema isolation verified: {schema_name}")
            
        except Exception as e:
            logger.error(f"CRITICAL: Tenant schema switch failed for {tenant_id}: {e}")
            # FAIL CLOSED - Never fall back to public schema
            abort(503, "Tenant isolation failure - service unavailable")
    
    @staticmethod
    def _validate_user_tenant_access(tenant):
        """Validate that current user has access to the specified tenant"""
        try:
            from flask_login import current_user
            from app.models import TenantUser
            
            # REQUIRE authentication for tenant access validation
            if not current_user or not current_user.is_authenticated:
                logger.warning("Tenant access validation requires authentication")
                return False
                
            # Check if user is associated with this tenant
            tenant_user = TenantUser.query.filter_by(
                tenant_id=tenant.id,
                user_id=current_user.id,
                is_active=True
            ).first()
            
            return tenant_user is not None
            
        except Exception as e:
            logger.error(f"Error validating tenant access: {e}")
            return False
    
    @staticmethod
    def reset_tenant_context():
        """Reset tenant context (rely on checkin events for connection reset)"""
        try:
            # Reset context variables only - connection reset handled by checkin event
            _tenant_schema_context.set('public')
            if hasattr(g, 'tenant_schema'):
                delattr(g, 'tenant_schema')
            if hasattr(g, 'tenant'):
                delattr(g, 'tenant')
                
        except Exception as e:
            logger.error(f"Error resetting tenant context: {e}")
    
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
    def _ensure_tenant_schema_and_tables(tenant_id, schema_name):
        """IDEMPOTENT: Ensure tenant schema and ALL required tables exist"""
        try:
            from app import db
            from app.models import LegalDocument, SearchQuery, SearchResult, AnalyticsEvent, UsageMetric
            from sqlalchemy import text
            
            # Validate PostgreSQL backend (required for schema isolation)
            if 'postgresql' not in str(db.engine.url).lower():
                logger.error("CRITICAL: Schema-based isolation requires PostgreSQL")
                return False
            
            # Create schema and tables in single transaction
            with db.engine.begin() as connection:
                # Create the schema
                connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
                
                # Set search path to tenant schema
                connection.execute(text(f'SET search_path = "{schema_name}", public'))
                
                # Create tenant-specific tables (only tenant-scoped models)
                tenant_models = [LegalDocument, SearchQuery, SearchResult, AnalyticsEvent, UsageMetric]
                for model in tenant_models:
                    # Create table in tenant schema with proper error handling
                    try:
                        model.__table__.create(bind=connection, checkfirst=True)
                    except Exception as table_error:
                        logger.error(f"Failed to create table {model.__tablename__} in {schema_name}: {table_error}")
                        return False
            
            logger.debug(f"Tenant schema and tables ensured: {schema_name}")
            return True
            
        except Exception as e:
            logger.error(f"CRITICAL: Failed to ensure tenant schema {schema_name}: {e}")
            return False
    
    @staticmethod
    def create_tenant_schema(tenant_id):
        """Create isolated schema for new tenant (wrapper for _ensure_tenant_schema_and_tables)"""
        safe_tenant_id = str(tenant_id).replace('-', '_')
        schema_name = f"tenant_{safe_tenant_id}"
        return TenantManager._ensure_tenant_schema_and_tables(tenant_id, schema_name)

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