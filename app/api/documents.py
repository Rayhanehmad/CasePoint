"""
API routes for document management with enhanced processing capabilities
"""
import os
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.legal import LegalDocument, DocumentType
from app.utils.document_processor import get_document_processor, process_file_for_legal_document
from app.utils.docker_processor import get_docker_processor, DockerSecurityError, VOLUME_NAME_REGEX
from app.core.tenant import TenantManager

# Create documents blueprint
documents_bp = Blueprint('documents', __name__)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@documents_bp.route('/upload', methods=['POST'])
@TenantManager.require_tenant()
def upload_document():
    """Upload and process a document with enhanced OCR and processing capabilities"""
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed',
                'allowed_extensions': list(current_app.config['ALLOWED_EXTENSIONS'])
            }), 400
        
        # Secure the filename
        if not file.filename:
            return jsonify({'error': 'Filename is required'}), 400
        filename = secure_filename(file.filename)
        original_filename = file.filename
        
        # Create upload directory if it doesn't exist
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create LegalDocument record
        legal_document = LegalDocument()
        legal_document.filename = filename
        legal_document.original_filename = original_filename
        legal_document.file_path = file_path
        legal_document.file_size = file_size
        legal_document.document_type = DocumentType.LEGAL_OPINION  # Default, will be updated by processor
        legal_document.processing_status = 'pending'
        legal_document.uploaded_by = current_user.id if current_user.is_authenticated else None
        
        db.session.add(legal_document)
        db.session.flush()  # Get ID without committing
        
        # Process the document
        processing_result = process_file_for_legal_document(file_path, legal_document)
        
        # Commit the changes
        db.session.commit()
        
        response_data = {
            'document_id': str(legal_document.id),
            'filename': original_filename,
            'file_size': file_size,
            'processing_status': legal_document.processing_status,
            'processing_result': processing_result,
            'document_type': legal_document.document_type.value if legal_document.document_type else None,
            'extraction_confidence': legal_document.extraction_confidence
        }
        
        if processing_result['success']:
            response_data.update({
                'extracted_text_preview': legal_document.extracted_text[:500] + '...' if len(legal_document.extracted_text) > 500 else legal_document.extracted_text,
                'word_count': processing_result.get('word_count', 0)
            })
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Document upload failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@documents_bp.route('/process-docker-volume', methods=['POST'])
@TenantManager.require_tenant()
def process_docker_volume():
    """Process documents from a Docker volume with bulletproof security validation"""
    try:
        # CRITICAL: Get tenant context for authorization
        tenant = TenantManager.get_current_tenant()
        if not tenant:
            return jsonify({'error': 'Tenant context required for volume access'}), 400
        
        data = request.get_json()
        if not data or 'volume_name' not in data:
            return jsonify({'error': 'Volume name is required'}), 400
        
        volume_name = data['volume_name']
        
        # CRITICAL: Validate volume name format before processing
        
        if not volume_name or not isinstance(volume_name, str):
            return jsonify({'error': 'Invalid volume name format'}), 400
        
        # Apply strict regex validation
        if not VOLUME_NAME_REGEX.match(volume_name):
            return jsonify({
                'error': 'Invalid volume name. Only alphanumeric characters, dots, underscores, and hyphens are allowed.',
                'volume_name': volume_name
            }), 400
        
        # CRITICAL: Check Docker availability with fail-fast
        from app.utils.health_checks import get_health_manager
        health_manager = get_health_manager()
        
        if not health_manager.is_feature_available('docker_processing'):
            error_response = health_manager.get_graceful_error_response('docker_processing')
            return jsonify(error_response), 503
        
        # CRITICAL: Verify tenant authorization for this volume
        from app.models.tenant import TenantVolume
        if not TenantVolume.is_volume_authorized(str(tenant.id), volume_name):
            current_app.logger.warning(f"SECURITY: Unauthorized volume access attempt by tenant {tenant.id}: {volume_name}")
            return jsonify({
                'error': 'Access denied: Volume not authorized for this tenant',
                'volume_name': volume_name
            }), 403
        
        # Get document processor
        processor = get_document_processor()
        
        # Process documents from the volume (processor handles tenant context internally)
        results = processor.process_docker_volume_documents(volume_name)
        
        # Create LegalDocument records for successful processing
        created_documents = []
        for result in results:
            if result['success']:
                try:
                    legal_document = LegalDocument()
                    legal_document.filename = result['filename']
                    legal_document.original_filename = result['filename']
                    legal_document.file_path = result['file_path']
                    legal_document.file_size = result['file_size']
                    legal_document.file_hash = result.get('file_hash')
                    legal_document.document_type = result.get('document_type', DocumentType.LEGAL_OPINION)
                    legal_document.extracted_text = result.get('extracted_text', '')
                    legal_document.processing_status = 'completed'
                    legal_document.extraction_confidence = result.get('confidence', 95) / 100 if 'confidence' in result else 0.95
                    legal_document.custom_metadata = {
                        'source': 'docker_volume',
                        'volume_name': volume_name,
                        'original_path': result.get('original_path'),
                        'processing_method': result.get('processing_method')
                    }
                    legal_document.uploaded_by = current_user.id if current_user.is_authenticated else None
                    
                    db.session.add(legal_document)
                    created_documents.append({
                        'filename': result['filename'],
                        'document_id': str(legal_document.id),
                        'processing_status': 'completed'
                    })
                    
                except Exception as e:
                    current_app.logger.error(f"Failed to create LegalDocument for {result['filename']}: {e}")
        
        db.session.commit()
        
        return jsonify({
            'volume_name': volume_name,
            'total_processed': len(results),
            'successful': len(created_documents),
            'failed': len(results) - len(created_documents),
            'created_documents': created_documents,
            'processing_summary': [
                {
                    'filename': r['filename'],
                    'success': r['success'],
                    'error': r.get('error')
                } for r in results
            ]
        }), 200
        
    except DockerSecurityError as e:
        db.session.rollback()
        current_app.logger.error(f"SECURITY: Docker volume processing blocked: {e}")
        return jsonify({
            'error': 'Security validation failed',
            'details': str(e),
            'status': 'security_error'
        }), 403
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Docker volume processing failed: {e}")
        return jsonify({
            'error': 'Internal server error',
            'status': 'error'
        }), 500

@documents_bp.route('/process-docker-container', methods=['POST'])
@TenantManager.require_tenant()
def process_docker_container():
    """Process documents from a Docker container with security validation"""
    try:
        # CRITICAL: Get tenant context for authorization
        tenant = TenantManager.get_current_tenant()
        if not tenant:
            return jsonify({'error': 'Tenant context required for container access'}), 400
        
        data = request.get_json()
        if not data or 'container_id' not in data:
            return jsonify({'error': 'Container ID is required'}), 400
        
        container_id = data['container_id']
        source_paths = data.get('source_paths')  # Optional
        
        # CRITICAL: Validate container ID format
        
        if not container_id or not isinstance(container_id, str):
            return jsonify({'error': 'Invalid container ID format'}), 400
        
        if len(container_id) > 100:
            return jsonify({'error': 'Container ID too long'}), 400
        
        # CRITICAL: Check Docker availability with fail-fast
        from app.utils.health_checks import get_health_manager
        health_manager = get_health_manager()
        
        if not health_manager.is_feature_available('docker_processing'):
            error_response = health_manager.get_graceful_error_response('docker_processing')
            return jsonify(error_response), 503
        
        # Get document processor
        processor = get_document_processor()
        
        # Process documents from the container (processor handles tenant context internally)
        results = processor.process_container_documents(container_id, source_paths)
        
        # Create LegalDocument records for successful processing
        created_documents = []
        for result in results:
            if result['success']:
                try:
                    legal_document = LegalDocument()
                    legal_document.filename = result['filename']
                    legal_document.original_filename = result['filename']
                    legal_document.file_path = result['file_path']
                    legal_document.file_size = result['file_size']
                    legal_document.file_hash = result.get('file_hash')
                    legal_document.document_type = result.get('document_type', DocumentType.LEGAL_OPINION)
                    legal_document.extracted_text = result.get('extracted_text', '')
                    legal_document.processing_status = 'completed'
                    legal_document.extraction_confidence = result.get('confidence', 95) / 100 if 'confidence' in result else 0.95
                    legal_document.custom_metadata = {
                        'source': 'docker_container',
                        'container_id': container_id,
                        'original_container_path': result.get('original_container_path'),
                        'processing_method': result.get('processing_method')
                    }
                    legal_document.uploaded_by = current_user.id if current_user.is_authenticated else None
                    
                    db.session.add(legal_document)
                    created_documents.append({
                        'filename': result['filename'],
                        'document_id': str(legal_document.id),
                        'processing_status': 'completed'
                    })
                    
                except Exception as e:
                    current_app.logger.error(f"Failed to create LegalDocument for {result['filename']}: {e}")
        
        db.session.commit()
        
        return jsonify({
            'container_id': container_id,
            'total_processed': len(results),
            'successful': len(created_documents),
            'failed': len(results) - len(created_documents),
            'created_documents': created_documents,
            'processing_summary': [
                {
                    'filename': r['filename'],
                    'success': r['success'],
                    'error': r.get('error')
                } for r in results
            ]
        }), 200
        
    except DockerSecurityError as e:
        db.session.rollback()
        current_app.logger.error(f"SECURITY: Docker container processing blocked: {e}")
        return jsonify({
            'error': 'Security validation failed',
            'details': str(e),
            'status': 'security_error'
        }), 403
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Docker container processing failed: {e}")
        return jsonify({
            'error': 'Internal server error',
            'status': 'error'
        }), 500

@documents_bp.route('/docker/volumes', methods=['GET'])
@TenantManager.require_tenant()
def list_docker_volumes():
    """List available Docker volumes with tenant authorization filtering"""
    try:
        # CRITICAL: Get tenant context for authorization
        tenant = TenantManager.get_current_tenant()
        if not tenant:
            return jsonify({'error': 'Tenant context required for volume listing'}), 400
        
        # CRITICAL: Check Docker availability with fail-fast
        from app.utils.health_checks import get_health_manager
        health_manager = get_health_manager()
        
        if not health_manager.is_feature_available('docker_processing'):
            error_response = health_manager.get_graceful_error_response('docker_processing')
            return jsonify(error_response), 503
        
        docker_processor = get_docker_processor()
        if not docker_processor:
            return jsonify({
                'error': 'Docker processor not available',
                'status': 'service_unavailable'
            }), 503
        
        # CRITICAL: Only list volumes authorized for this tenant
        volumes = docker_processor.volume_manager.list_available_volumes(tenant_id=str(tenant.id))
        
        # Also include volume authorization details
        from app.models.tenant import TenantVolume
        authorized_volumes = TenantVolume.get_tenant_volumes(str(tenant.id))
        
        volume_details = []
        for volume_name in volumes:
            auth_info = next((v for v in authorized_volumes if v.volume_name == volume_name), None)
            volume_details.append({
                'name': volume_name,
                'access_level': auth_info.access_level if auth_info else 'unknown',
                'authorized': auth_info is not None,
                'description': auth_info.description if auth_info else None
            })
        
        return jsonify({
            'volumes': volume_details,
            'total_authorized': len(authorized_volumes),
            'tenant_id': str(tenant.id)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to list Docker volumes: {e}")
        return jsonify({
            'error': 'Internal server error',
            'status': 'error'
        }), 500

@documents_bp.route('/docker/containers', methods=['GET'])
@TenantManager.require_tenant()
def list_docker_containers():
    """List available Docker containers with security validation"""
    try:
        # CRITICAL: Get tenant context for logging
        tenant = TenantManager.get_current_tenant()
        if not tenant:
            return jsonify({'error': 'Tenant context required for container listing'}), 400
        
        # CRITICAL: Check Docker availability with fail-fast
        from app.utils.health_checks import get_health_manager
        health_manager = get_health_manager()
        
        if not health_manager.is_feature_available('docker_processing'):
            error_response = health_manager.get_graceful_error_response('docker_processing')
            return jsonify(error_response), 503
        
        docker_processor = get_docker_processor()
        if not docker_processor:
            return jsonify({
                'error': 'Docker processor not available',
                'status': 'service_unavailable'
            }), 503
        
        containers = docker_processor.list_containers_with_documents()
        
        # Log container access for security audit
        current_app.logger.info(f"Tenant {tenant.id} accessed container list: {len(containers)} containers found")
        
        return jsonify({
            'containers': containers,
            'tenant_id': str(tenant.id),
            'total_found': len(containers)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to list Docker containers: {e}")
        return jsonify({
            'error': 'Internal server error',
            'status': 'error'
        }), 500

@documents_bp.route('/<document_id>', methods=['GET'])
@TenantManager.require_tenant()
def get_document(document_id):
    """Get document details"""
    try:
        document = LegalDocument.query.get_or_404(document_id)
        
        return jsonify({
            'id': str(document.id),
            'filename': document.original_filename,
            'file_size': document.file_size,
            'file_size_mb': document.file_size_mb,
            'document_type': document.document_type.value if document.document_type else None,
            'processing_status': document.processing_status,
            'extraction_confidence': document.extraction_confidence,
            'extracted_text': document.extracted_text,
            'word_count': len(document.extracted_text.split()) if document.extracted_text else 0,
            'created_at': document.created_at.isoformat(),
            'custom_metadata': document.custom_metadata
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get document {document_id}: {e}")
        return jsonify({'error': 'Document not found'}), 404

@documents_bp.route('/<document_id>', methods=['DELETE'])
@TenantManager.require_tenant()
def delete_document(document_id):
    """Delete a document"""
    try:
        document = LegalDocument.query.get_or_404(document_id)
        
        # Delete the file if it exists
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete the database record
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'message': 'Document deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete document {document_id}: {e}")
        return jsonify({'error': 'Failed to delete document'}), 500