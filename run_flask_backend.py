#!/usr/bin/env python3
"""
Run script for Flask backend
"""

import sys
import os

# Add backend_flask to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend_flask'))

from app import create_app

if __name__ == '__main__':
    print("🚀 Starting KanoonPK Flask Backend on port 5000...")
    app = create_app('default')
    app.run(host='0.0.0.0', port=5000, debug=True)
