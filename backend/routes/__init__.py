"""
Routes/Blueprints for KanoonPK
"""

from routes.auth_routes import auth_bp, login_required, admin_required
from routes.case_routes import case_bp
from routes.act_routes import act_bp
from routes.admin_routes import admin_bp
from routes.ai_routes import ai_bp

__all__ = ['auth_bp', 'case_bp', 'act_bp', 'admin_bp', 'ai_bp', 'login_required', 'admin_required']
