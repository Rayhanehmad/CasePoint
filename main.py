#!/usr/bin/env python3
"""
KanoonPK - Main Entry Point
Imports the modular Flask backend from backend/
This file is kept for backward compatibility with the gunicorn workflow
"""

import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the Flask app from the modular backend
from app import create_app

# Create the Flask application instance
app = create_app('default')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
