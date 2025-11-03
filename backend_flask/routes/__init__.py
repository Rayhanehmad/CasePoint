"""
Routes/Blueprints for KanoonPK
"""

from .auth_routes import auth_bp
from .case_routes import case_bp
from .act_routes import act_bp
from .admin_routes import admin_bp
from .ai_routes import ai_bp

__all__ = ['auth_bp', 'case_bp', 'act_bp', 'admin_bp', 'ai_bp']
