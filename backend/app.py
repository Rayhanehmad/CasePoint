"""
CasePoint Flask Backend - Main Application
Professional Legal Research Platform with AI, OCR, and Vector Search
"""

import os
import logging
from flask import Flask, render_template, url_for, session
from flask_cors import CORS
from datetime import datetime

# Import configuration
from config import config

# Import models
from models import db
from models.user import User
from models.case import LegalCitation

# Import routes
from routes import auth_bp, case_bp, act_bp, admin_bp, ai_bp

# Configure logging
logging.basicConfig(level=logging.INFO)

def create_app(config_name='default'):
    """Application factory pattern"""
    
    # Initialize Flask app
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize CORS for React frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        },
        r"/auth/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "supports_credentials": True
        }
    })
    
    # Initialize database
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
        logging.info("Database tables created successfully")
    
    # Initialize Flask-Admin
    from admin import init_admin
    init_admin(app)
    
    # Track user activity
    @app.before_request
    def track_user_activity():
        """Update last_seen timestamp for logged-in users"""
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                user.last_seen = datetime.utcnow()
                db.session.commit()
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(case_bp, url_prefix='/cases')
    app.register_blueprint(act_bp, url_prefix='/acts')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')  # Changed to avoid conflict with Flask-Admin
    app.register_blueprint(ai_bp, url_prefix='/ai')
    
    # Register consolidated API routes for React frontend
    from routes.api_routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register multi-PDF upload route
    from routes.upload_multi_pdf import upload_multi_pdf_bp
    app.register_blueprint(upload_multi_pdf_bp)
    
    # Main routes
    @app.route('/')
    def home():
        """Homepage with search interface"""
        # Get statistics
        try:
            total_citations = LegalCitation.query.count()
            total_cases = LegalCitation.query.filter_by(document_type='case').count()
            total_acts = LegalCitation.query.filter(
                LegalCitation.document_type.in_(['act', 'statute'])
            ).count()
        except Exception as e:
            logging.error(f"Error fetching statistics: {e}")
            total_citations = 0
            total_cases = 0
            total_acts = 0
        
        stats = {
            'total_citations': total_citations,
            'total_cases': total_cases,
            'total_acts': total_acts
        }
        
        return render_template('home.html', stats=stats)
    
    @app.route('/search')
    def search():
        """General search results page"""
        from flask import request
        from services.utils_extract_parties import extract_parties
        query = request.args.get('q', '')
        category = request.args.get('category', 'all')
        
        results = []
        
        if query:
            if category == 'all' or category == 'cases':
                cases = LegalCitation.query.filter(
                    LegalCitation.document_type == 'case',
                    (LegalCitation.title.ilike(f'%{query}%')) |
                    (LegalCitation.citation.ilike(f'%{query}%')) |
                    (LegalCitation.summary.ilike(f'%{query}%')) |
                    (LegalCitation.full_text.ilike(f'%{query}%')) |
                    (LegalCitation.keywords.ilike(f'%{query}%'))
                ).all()
                results.extend(cases)
            
            if category == 'all' or category == 'acts':
                acts = LegalCitation.query.filter(
                    LegalCitation.document_type.in_(['act', 'statute']),
                    (LegalCitation.title.ilike(f'%{query}%')) |
                    (LegalCitation.citation.ilike(f'%{query}%')) |
                    (LegalCitation.full_text.ilike(f'%{query}%')) |
                    (LegalCitation.keywords.ilike(f'%{query}%'))
                ).all()
                results.extend(acts)
        
        # Extract party names for each result
        for result in results:
            result.party_line = extract_parties(result.full_text, result.journal)
        
        breadcrumbs = [{'text': 'Search Results', 'url': url_for('search')}]
        return render_template('search_results.html', 
                             results=results, 
                             query=query, 
                             category=category,
                             breadcrumbs=breadcrumbs)
    
    @app.route('/upload/multi-pdf')
    def upload_multi_pdf_page():
        """Multi-PDF citation upload page (admin only)"""
        # Check if user is admin
        if session.get('role') != 'admin':
            from flask import flash, redirect, url_for
            flash('You must be an admin to access this page.', 'danger')
            return redirect(url_for('home'))
        
        return render_template('upload_multi_pdf.html')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        from flask import jsonify
        return jsonify({
            'status': 'healthy',
            'service': 'casepoint-flask',
            'version': '2.0.0'
        })
    
    @app.route('/api/health')
    def api_health():
        """API health check"""
        from flask import jsonify
        return jsonify({
            'status': 'healthy',
            'backend': 'flask',
            'version': '2.0.0',
            'database': 'connected'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'default'))
    app.run(host='0.0.0.0', port=5000, debug=True)
