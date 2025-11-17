"""
CasePoint Flask Backend - Main Application
Professional Legal Research Platform with AI, OCR, and Vector Search
"""

import os
import logging
from flask import Flask, send_from_directory, session, jsonify
from flask_cors import CORS
from datetime import datetime

# Import configuration
from config import config

# Import models
from models import db
from models.user import User
from models.case import LegalCitation
from models.shared_excerpt import SharedExcerpt

# Configure logging
logging.basicConfig(level=logging.INFO)

def create_app(config_name='default'):
    """Application factory pattern"""
    
    # Initialize Flask app - serve React build
    app = Flask(__name__,
                static_folder='../frontend/dist',
                static_url_path='')
    
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
        },
        r"/ai/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
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
    
    # Register API-only blueprints
    from routes.api_routes import api_bp
    from routes.auth_routes import auth_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Health check endpoint
    @app.route('/api/health')
    def api_health():
        """API health check"""
        return jsonify({
            'status': 'healthy',
            'backend': 'flask',
            'version': '2.0.0',
            'database': 'connected'
        })
    
    # Serve React App - catch-all route for SPA
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react(path):
        """Serve React SPA for all non-API routes"""
        # If path is a file in dist folder, serve it
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        # Otherwise serve index.html for client-side routing
        return send_from_directory(app.static_folder, 'index.html')
    
    return app


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'default'))
    app.run(host='0.0.0.0', port=5000, debug=True)
