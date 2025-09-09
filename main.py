"""
Main entry point for KanoonPK SaaS Legal Research Platform
"""
from saas_main import app

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )