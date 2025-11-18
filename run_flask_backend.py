#!/usr/bin/env python3
"""
Run script for Flask backend
"""

import os
import sys

# Add backend folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app

if __name__ == '__main__':
    print("🚀 Starting KanoonPK Flask Backend on port 5000...")
    app = create_app(os.getenv("FLASK_ENV", "default"))
    app.run(host='0.0.0.0', port=5000, debug=True)
