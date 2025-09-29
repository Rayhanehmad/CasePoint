#!/usr/bin/env python3
"""
KanoonPK SaaS Application Launcher
Starts both FastAPI backend and React frontend
"""

import os
import sys
import subprocess
import time
import threading

def run_backend():
    """Start FastAPI backend server"""
    print("🚀 Starting FastAPI backend on port 8000...")
    os.chdir('backend')
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        'DATABASE_URL': os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/postgres'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
        'STRIPE_SECRET_KEY': os.getenv('STRIPE_SECRET_KEY', ''),
    })
    
    subprocess.run([
        sys.executable, '-m', 'uvicorn', 
        'main:app', 
        '--host', '0.0.0.0', 
        '--port', '8000', 
        '--reload'
    ], env=env)

def run_frontend():
    """Start React frontend development server"""
    print("🎨 Starting React frontend on port 5000...")
    time.sleep(3)  # Give backend time to start
    os.chdir('frontend')
    subprocess.run(['npm', 'run', 'dev'])

def main():
    """Main application launcher"""
    print("🏛️  KanoonPK SaaS Legal Research Platform")
    print("=" * 50)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    # Start frontend in main thread
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down KanoonPK SaaS...")
        sys.exit(0)

if __name__ == "__main__":
    main()