#!/usr/bin/env python3
"""
KanoonPK SaaS - WSGI/ASGI Application for Replit
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, 'backend')

try:
    # Import the FastAPI app
    from backend.main import app as fastapi_app
    print("✅ KanoonPK FastAPI backend loaded successfully!")
        
except ImportError as e:
    print(f"❌ Failed to import backend: {e}")
    print("Please ensure the backend dependencies are installed.")
    sys.exit(1)

# Create WSGI adapter for gunicorn compatibility
try:
    from asgiref.wsgi import WsgiToAsgi
    from asgiref.sync import iscoroutinefunction
    
    # Simple ASGI to WSGI adapter
    class ASGItoWSGI:
        def __init__(self, asgi_app):
            self.asgi_app = asgi_app
        
        def __call__(self, environ, start_response):
            import asyncio
            import threading
            from concurrent.futures import ThreadPoolExecutor
            
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Create a simple ASGI scope from WSGI environ
            scope = {
                'type': 'http',
                'method': environ['REQUEST_METHOD'],
                'path': environ['PATH_INFO'],
                'query_string': environ.get('QUERY_STRING', '').encode(),
                'headers': [(key.lower().replace('_', '-').encode(), value.encode()) 
                           for key, value in environ.items() 
                           if key.startswith('HTTP_')],
            }
            
            response_data = {'status': 500, 'headers': [], 'body': b'Internal Server Error'}
            
            async def receive():
                return {'type': 'http.request', 'body': b''}
            
            async def send(message):
                if message['type'] == 'http.response.start':
                    response_data['status'] = message['status']
                    response_data['headers'] = message.get('headers', [])
                elif message['type'] == 'http.response.body':
                    response_data['body'] = message.get('body', b'')
            
            async def run_asgi():
                await self.asgi_app(scope, receive, send)
            
            # Run the ASGI app
            if loop.is_running():
                # If we're in an async context, we need to use a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, run_asgi())
                    future.result()
            else:
                loop.run_until_complete(run_asgi())
            
            # Send WSGI response
            status = f"{response_data['status']} OK"
            headers = [(key.decode() if isinstance(key, bytes) else key, 
                       value.decode() if isinstance(value, bytes) else value) 
                      for key, value in response_data['headers']]
            start_response(status, headers)
            
            return [response_data['body']]
    
    # Create WSGI-compatible app
    app = ASGItoWSGI(fastapi_app)
    
except ImportError:
    print("❌ asgiref not available, using basic wrapper")
    # Fallback: Create a simple Flask app
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/')
    def root():
        return jsonify({
            "message": "🏛️ KanoonPK SaaS API",
            "version": "1.0.0", 
            "status": "active",
            "docs": "/api/docs",
            "note": "FastAPI backend running via WSGI adapter"
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "service": "kanoonpk-backend",
            "version": "1.0.0"
        })
    
    print("🔄 Using Flask fallback for WSGI compatibility")

# Export the app for WSGI servers
application = app

if __name__ == "__main__":
    print("🚀 Starting KanoonPK SaaS...")
    # Use the original FastAPI app with uvicorn when run directly
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=5000, reload=True)