"""
Health check API endpoints for system monitoring and dependency validation
"""
from flask import Blueprint, jsonify, current_app
from app.utils.health_checks import get_health_manager

# Create health blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Get system health status"""
    try:
        health_manager = get_health_manager()
        health_status = health_manager.get_system_health()
        
        # Return appropriate HTTP status based on health
        if health_status['status'] == 'healthy':
            return jsonify(health_status), 200
        else:
            return jsonify(health_status), 503
            
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': 'Health check system failure',
            'details': str(e)
        }), 500

@health_bp.route('/health/dependencies', methods=['GET'])
def dependencies_check():
    """Get detailed dependency status"""
    try:
        health_manager = get_health_manager()
        health_status = health_manager.get_system_health()
        
        return jsonify({
            'dependencies': health_status['dependencies'],
            'missing_critical': health_manager.get_missing_dependencies(),
            'timestamp': health_status['timestamp']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Dependencies check failed: {e}")
        return jsonify({
            'error': 'Dependencies check failure',
            'details': str(e)
        }), 500

@health_bp.route('/health/features', methods=['GET'])
def features_check():
    """Get feature availability status"""
    try:
        health_manager = get_health_manager()
        features = health_manager.get_feature_availability()
        
        return jsonify({
            'features': features,
            'summary': {
                'total_features': len(features),
                'available_features': len([f for f in features.values() if f['available']]),
                'unavailable_features': len([f for f in features.values() if not f['available']])
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Features check failed: {e}")
        return jsonify({
            'error': 'Features check failure',
            'details': str(e)
        }), 500