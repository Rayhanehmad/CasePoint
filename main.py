#!/usr/bin/env python3
"""
KanoonPK SaaS - Simple launcher for Replit workflow
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, 'backend')

try:
    # Import and run the FastAPI app
    from backend.main import app
    print("✅ KanoonPK FastAPI backend loaded successfully!")
    
    if __name__ == "__main__":
        import uvicorn
        print("🚀 Starting KanoonPK SaaS on port 5000...")
        uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)
        
except ImportError as e:
    print(f"❌ Failed to import backend: {e}")
    print("Please ensure the backend dependencies are installed.")
    sys.exit(1)