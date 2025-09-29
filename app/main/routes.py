"""
Main routes for public pages
"""
from flask import render_template, jsonify, current_app
from app.main import main_bp

@main_bp.route('/')
def public_home():
    """Public home page"""
    return jsonify({
        'message': 'Welcome to KanoonPK - Smart Legal Research Platform',
        'tagline': 'Smart Legal Research, Instant AI search through Pakistan\'s Leading Law Reports',
        'version': '2.0.0',
        'status': 'active',
        'features': [
            'AI-Powered Legal Search',
            'Citation & Judgment Search', 
            'Advanced Search Filters',
            'Multi-Tenant SaaS Platform',
            'Pakistan Law Database'
        ]
    })

@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': current_app.config.get('startup_time', 'unknown'),
        'database': 'connected'
    })

@main_bp.route('/features')
def features():
    """Public features page"""
    return jsonify({
        'features': {
            'search': [
                'AI-Powered Legal Search',
                'Citation Search (PLD, SCMR, CLR, MLD)',
                'Advanced Boolean Search',
                'Precedent Analysis'
            ],
            'documents': [
                'Document Upload & Processing',
                'Automatic Legal Classification',
                'Citation Extraction',
                'Full-Text Search'
            ],
            'collaboration': [
                'Multi-User Tenants',
                'Shared Workspaces', 
                'Team Collaboration',
                'Role-Based Access'
            ],
            'analytics': [
                'Usage Analytics',
                'Search Insights',
                'Performance Metrics',
                'Custom Reports'
            ]
        }
    })

@main_bp.route('/api/v1/public/status')
def api_status():
    """Public API status endpoint"""
    return jsonify({
        'api_version': 'v1',
        'status': 'operational',
        'endpoints': {
            'auth': '/auth/',
            'search': '/search/',
            'documents': '/api/v1/documents',
            'analytics': '/analytics/'
        }
    })