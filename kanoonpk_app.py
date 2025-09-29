"""
KanoonPK - Modern SaaS Legal Research Platform
Main application entry point with modern architecture
"""
import os
from app import create_app, db

# Create Flask application using factory pattern
app = create_app(os.getenv('FLASK_ENV', 'development'))

# Create database tables
with app.app_context():
    # Import all models to ensure they're registered
    from app.models import *
    
    # Create all database tables
    db.create_all()
    
    # Initialize default data if needed
    from app.core.init_data import initialize_default_data
    initialize_default_data()

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('DEBUG', False)
    )