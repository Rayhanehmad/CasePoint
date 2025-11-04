"""
Flask-Admin configuration for KanoonPK
Web-based admin interface for managing users, cases, acts, and rules
"""

from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, session, flash
from models import db
from models.user import User
from models.case import LegalCitation


class SecureAdminIndexView(AdminIndexView):
    """Custom admin index view with authentication"""
    
    @expose('/')
    def index(self):
        # Check if user is admin
        if 'user_id' not in session:
            flash('Please login to access admin panel', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin():
            flash('Admin access required', 'error')
            return redirect(url_for('home'))
        
        # Get statistics
        total_cases = LegalCitation.query.filter_by(document_type='case').count()
        total_acts = LegalCitation.query.filter(
            LegalCitation.document_type.in_(['act', 'statute'])
        ).count()
        total_rules = LegalCitation.query.filter_by(document_type='rule').count()
        total_users = User.query.count()
        
        return self.render('admin/index.html',
                          total_cases=total_cases,
                          total_acts=total_acts,
                          total_rules=total_rules,
                          total_users=total_users)


class SecureModelView(ModelView):
    """Base model view with authentication"""
    
    def is_accessible(self):
        """Check if user is admin"""
        if 'user_id' not in session:
            return False
        
        user = User.query.get(session['user_id'])
        return user and user.is_admin()
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login if not accessible"""
        flash('Admin access required', 'error')
        return redirect(url_for('auth.login'))


class UserAdminView(SecureModelView):
    """User management view"""
    
    column_list = ['id', 'username', 'email', 'role', 'created_at', 'last_seen']
    column_searchable_list = ['username', 'email']
    column_filters = ['role', 'created_at']
    column_editable_list = ['role']
    
    # Don't show password hash
    form_excluded_columns = ['password_hash', 'citations']
    
    # Add custom column formatters
    column_formatters = {
        'last_seen': lambda v, c, m, p: m.last_seen.strftime('%Y-%m-%d %H:%M') if m.last_seen else 'Never',
        'created_at': lambda v, c, m, p: m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else ''
    }


class LegalCitationAdminView(SecureModelView):
    """Legal citations management view"""
    
    column_list = ['id', 'document_type', 'title', 'citation', 'court', 'year', 'legal_area', 'created_at']
    column_searchable_list = ['title', 'citation', 'court', 'summary']
    column_filters = ['document_type', 'year', 'court', 'legal_area', 'jurisdiction']
    column_editable_list = ['document_type', 'legal_area']
    column_default_sort = ('created_at', True)
    
    # Configure form
    form_excluded_columns = ['vector_id', 'uploader']
    
    # Limit results per page
    page_size = 50
    
    # Add custom column formatters
    column_formatters = {
        'title': lambda v, c, m, p: m.title[:50] + '...' if len(m.title) > 50 else m.title,
        'created_at': lambda v, c, m, p: m.created_at.strftime('%Y-%m-%d') if m.created_at else ''
    }
    
    # Enable export
    can_export = True
    export_types = ['csv', 'xlsx']


def init_admin(app):
    """Initialize Flask-Admin"""
    
    admin = Admin(
        app,
        name='KanoonPK Admin',
        index_view=SecureAdminIndexView()
    )
    
    # Add model views
    admin.add_view(UserAdminView(User, db.session, name='Users', category='User Management'))
    admin.add_view(LegalCitationAdminView(LegalCitation, db.session, name='All Citations', category='Legal Data', endpoint='all_citations'))
    
    # Add views for different document types
    class CaseView(LegalCitationAdminView):
        def get_query(self):
            return self.session.query(self.model).filter(self.model.document_type == 'case')
        
        def get_count_query(self):
            return self.session.query(self.model).filter(self.model.document_type == 'case')
    
    class ActView(LegalCitationAdminView):
        def get_query(self):
            return self.session.query(self.model).filter(
                self.model.document_type.in_(['act', 'statute'])
            )
        
        def get_count_query(self):
            return self.session.query(self.model).filter(
                self.model.document_type.in_(['act', 'statute'])
            )
    
    class RuleView(LegalCitationAdminView):
        def get_query(self):
            return self.session.query(self.model).filter(self.model.document_type == 'rule')
        
        def get_count_query(self):
            return self.session.query(self.model).filter(self.model.document_type == 'rule')
    
    admin.add_view(CaseView(LegalCitation, db.session, name='Cases Only', category='Legal Data', endpoint='cases_only'))
    admin.add_view(ActView(LegalCitation, db.session, name='Acts & Statutes', category='Legal Data', endpoint='acts_statutes'))
    admin.add_view(RuleView(LegalCitation, db.session, name='Rules Only', category='Legal Data', endpoint='rules_only'))
    
    return admin
