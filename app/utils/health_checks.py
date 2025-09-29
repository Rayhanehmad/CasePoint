"""
System health checks and dependency validation utilities
"""
import os
import subprocess
import logging
import importlib
from typing import Dict, Any, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class HealthCheckManager:
    """Manages system health checks and dependency validation"""
    
    def __init__(self):
        self.checks_cache = {}
        self.cache_timeout = 300  # 5 minutes cache
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        health_status = {
            'status': 'healthy',
            'timestamp': self._get_timestamp(),
            'dependencies': {},
            'features': {},
            'errors': [],
            'warnings': []
        }
        
        # Check all critical dependencies
        dependencies = [
            'tesseract', 'docker', 'pypdf2', 'python_docx', 
            'pytesseract', 'pillow', 'flask_sqlalchemy'
        ]
        
        for dep in dependencies:
            check_method = getattr(self, f'check_{dep}', None)
            if check_method:
                result = check_method()
                health_status['dependencies'][dep] = result
                
                if not result['available']:
                    if result.get('critical', False):
                        health_status['status'] = 'unhealthy'
                        health_status['errors'].append(result.get('error', f'{dep} unavailable'))
                    else:
                        health_status['warnings'].append(result.get('error', f'{dep} unavailable'))
        
        # Check feature availability
        health_status['features'] = self.get_feature_availability()
        
        return health_status
    
    def check_tesseract(self) -> Dict[str, Any]:
        """Check if Tesseract OCR is available"""
        try:
            # Try to run tesseract --version
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_info = result.stdout.strip().split('\n')[0]
                return {
                    'available': True,
                    'version': version_info,
                    'critical': False
                }
            else:
                return {
                    'available': False,
                    'error': 'Tesseract command failed',
                    'critical': False
                }
                
        except FileNotFoundError:
            return {
                'available': False,
                'error': 'Tesseract not found in PATH',
                'critical': False,
                'install_hint': 'Install with: sudo apt-get install tesseract-ocr'
            }
        except subprocess.TimeoutExpired:
            return {
                'available': False,
                'error': 'Tesseract command timeout',
                'critical': False
            }
        except Exception as e:
            return {
                'available': False,
                'error': f'Tesseract check failed: {str(e)}',
                'critical': False
            }
    
    def check_docker(self) -> Dict[str, Any]:
        """Check if Docker CLI is available with enhanced validation"""
        try:
            # Check docker --version first
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_info = result.stdout.strip()
                
                # Additional check: try to list volumes (tests actual Docker daemon access)
                try:
                    volume_result = subprocess.run(['docker', 'volume', 'ls'], 
                                                 capture_output=True, text=True, timeout=15)
                    daemon_available = volume_result.returncode == 0
                    
                    return {
                        'available': True,
                        'version': version_info,
                        'critical': False,
                        'daemon_accessible': daemon_available,
                        'docker_features': ['cli', 'daemon'] if daemon_available else ['cli'],
                        'warning': None if daemon_available else 'Docker daemon not accessible - some features may not work'
                    }
                except Exception:
                    return {
                        'available': True,
                        'version': version_info,
                        'critical': False,
                        'daemon_accessible': False,
                        'docker_features': ['cli'],
                        'warning': 'Docker CLI available but daemon not accessible'
                    }
            else:
                return {
                    'available': False,
                    'error': 'Docker command failed',
                    'critical': False
                }
                
        except FileNotFoundError:
            return {
                'available': False,
                'error': 'Docker not found in PATH - Docker features disabled',
                'critical': False,
                'install_hint': 'Install Docker CLI for Docker volume processing features',
                'fail_fast_feature': 'docker_processing'
            }
        except subprocess.TimeoutExpired:
            return {
                'available': False,
                'error': 'Docker command timeout - may indicate system issues',
                'critical': False
            }
        except Exception as e:
            return {
                'available': False,
                'error': f'Docker check failed: {str(e)}',
                'critical': False
            }
    
    def check_pypdf2(self) -> Dict[str, Any]:
        """Check if PyPDF2 is available with fail-fast validation"""
        try:
            import PyPDF2
            # Test basic functionality
            version = getattr(PyPDF2, '__version__', 'unknown')
            
            # Verify PdfReader is available (critical for PDF processing)
            if not hasattr(PyPDF2, 'PdfReader'):
                return {
                    'available': False,
                    'error': 'PyPDF2 PdfReader not available - outdated version',
                    'critical': True,
                    'install_hint': 'Update with: pip install --upgrade PyPDF2'
                }
            
            return {
                'available': True,
                'version': version,
                'critical': True,
                'features': ['PdfReader', 'text_extraction']
            }
        except ImportError as e:
            return {
                'available': False,
                'error': 'PyPDF2 not installed - CRITICAL for PDF processing',
                'critical': True,
                'install_hint': 'Install with: pip install PyPDF2',
                'fail_fast': True
            }
    
    def check_python_docx(self) -> Dict[str, Any]:
        """Check if python-docx is available with fail-fast validation"""
        try:
            from docx import Document
            import docx
            
            # Test basic functionality
            version = getattr(docx, '__version__', 'unknown')
            
            # Verify Document class is functional
            if not callable(Document):
                return {
                    'available': False,
                    'error': 'python-docx Document class not functional',
                    'critical': True,
                    'install_hint': 'Reinstall with: pip install --force-reinstall python-docx'
                }
            
            return {
                'available': True,
                'version': version,
                'critical': True,
                'features': ['Document', 'text_extraction']
            }
        except ImportError:
            return {
                'available': False,
                'error': 'python-docx not installed - CRITICAL for DOCX processing',
                'critical': True,
                'install_hint': 'Install with: pip install python-docx',
                'fail_fast': True
            }
    
    def check_pytesseract(self) -> Dict[str, Any]:
        """Check if pytesseract is available"""
        try:
            import pytesseract
            
            # Also check if it can connect to tesseract binary
            tesseract_check = self.check_tesseract()
            if tesseract_check['available']:
                try:
                    pytesseract.get_tesseract_version()
                    return {
                        'available': True,
                        'version': getattr(pytesseract, '__version__', 'unknown'),
                        'critical': False,
                        'tesseract_binary': 'available'
                    }
                except Exception as e:
                    return {
                        'available': False,
                        'error': f'pytesseract cannot connect to tesseract: {str(e)}',
                        'critical': False
                    }
            else:
                return {
                    'available': False,
                    'error': 'pytesseract available but tesseract binary missing',
                    'critical': False
                }
                
        except ImportError:
            return {
                'available': False,
                'error': 'pytesseract not installed',
                'critical': False,
                'install_hint': 'Install with: pip install pytesseract'
            }
    
    def check_pillow(self) -> Dict[str, Any]:
        """Check if Pillow (PIL) is available"""
        try:
            from PIL import Image
            import PIL
            return {
                'available': True,
                'version': PIL.__version__,
                'critical': False
            }
        except ImportError:
            return {
                'available': False,
                'error': 'Pillow (PIL) not installed',
                'critical': False,
                'install_hint': 'Install with: pip install Pillow'
            }
    
    def check_flask_sqlalchemy(self) -> Dict[str, Any]:
        """Check if Flask-SQLAlchemy is available"""
        try:
            import flask_sqlalchemy
            return {
                'available': True,
                'version': flask_sqlalchemy.__version__,
                'critical': True
            }
        except ImportError:
            return {
                'available': False,
                'error': 'Flask-SQLAlchemy not installed',
                'critical': True
            }
    
    def get_feature_availability(self) -> Dict[str, Any]:
        """Get availability of major features"""
        features = {}
        
        # PDF Processing
        pypdf2_check = self.check_pypdf2()
        features['pdf_processing'] = {
            'available': pypdf2_check['available'],
            'dependencies': ['pypdf2'],
            'description': 'PDF text extraction and processing'
        }
        
        # DOCX Processing
        docx_check = self.check_python_docx()
        features['docx_processing'] = {
            'available': docx_check['available'],
            'dependencies': ['python_docx'],
            'description': 'Microsoft Word document processing'
        }
        
        # OCR Processing
        tesseract_check = self.check_tesseract()
        pytesseract_check = self.check_pytesseract()
        pillow_check = self.check_pillow()
        
        ocr_available = (tesseract_check['available'] and 
                        pytesseract_check['available'] and 
                        pillow_check['available'])
        
        features['ocr_processing'] = {
            'available': ocr_available,
            'dependencies': ['tesseract', 'pytesseract', 'pillow'],
            'description': 'Optical Character Recognition for images'
        }
        
        # Docker Processing
        docker_check = self.check_docker()
        features['docker_processing'] = {
            'available': docker_check['available'],
            'dependencies': ['docker'],
            'description': 'Document processing from Docker containers and volumes'
        }
        
        return features
    
    def get_missing_dependencies(self) -> List[Dict[str, Any]]:
        """Get list of missing critical dependencies"""
        health = self.get_system_health()
        missing = []
        
        for dep_name, dep_info in health['dependencies'].items():
            if not dep_info['available'] and dep_info.get('critical', False):
                missing.append({
                    'name': dep_name,
                    'error': dep_info.get('error', 'Not available'),
                    'install_hint': dep_info.get('install_hint', 'See documentation')
                })
        
        return missing
    
    def is_feature_available(self, feature_name: str) -> bool:
        """Check if a specific feature is available"""
        features = self.get_feature_availability()
        return features.get(feature_name, {}).get('available', False)
    
    def get_graceful_error_response(self, feature_name: str) -> Dict[str, Any]:
        """Get a graceful error response when a feature is unavailable"""
        features = self.get_feature_availability()
        feature_info = features.get(feature_name, {})
        
        if feature_info.get('available', False):
            return {
                'error': None,
                'feature': feature_name,
                'description': feature_info.get('description', 'Feature available'),
                'status': 'available'
            }
        
        missing_deps = []
        for dep in feature_info.get('dependencies', []):
            health = self.get_system_health()
            if not health['dependencies'].get(dep, {}).get('available', False):
                missing_deps.append({
                    'name': dep,
                    'error': health['dependencies'][dep].get('error', 'Not available'),
                    'install_hint': health['dependencies'][dep].get('install_hint', '')
                })
        
        return {
            'error': f'{feature_name} is not available',
            'feature': feature_name,
            'description': feature_info.get('description', 'Feature unavailable'),
            'missing_dependencies': missing_deps,
            'status': 'service_unavailable'
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

# Global health check manager instance
health_manager = HealthCheckManager()

def get_health_manager() -> HealthCheckManager:
    """Get the global health check manager"""
    return health_manager

def is_dependency_available(dependency_name: str) -> bool:
    """Quick check if a dependency is available"""
    health = health_manager.get_system_health()
    return health['dependencies'].get(dependency_name, {}).get('available', False)

def require_feature(feature_name: str):
    """Decorator to require a feature to be available"""
    def decorator(f):
        from functools import wraps
        from flask import jsonify
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not health_manager.is_feature_available(feature_name):
                error_response = health_manager.get_graceful_error_response(feature_name)
                return jsonify(error_response), 503
            return f(*args, **kwargs)
        return decorated_function
    return decorator