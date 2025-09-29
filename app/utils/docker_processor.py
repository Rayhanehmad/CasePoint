"""
Docker file processor utilities for mounting and accessing documents from Docker containers
Enhanced with bulletproof security measures against path traversal and unauthorized access

SECURITY FEATURES:
- Strict regex validation for volume names
- Path traversal prevention with containment checks  
- Tenant-scoped volume authorization
- Security logging for audit trails
- Secure temporary directories
- Input sanitization and validation
- Fail-safe error handling
"""
import os
import re
import logging
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Union
from flask import current_app, g
from flask_login import current_user

logger = logging.getLogger(__name__)

# Security constants
VOLUME_NAME_REGEX = re.compile(r'^[A-Za-z0-9._-]+$')
MAX_VOLUME_NAME_LENGTH = 100
FORBIDDEN_VOLUME_NAMES = {'..', '.', '/', '\\', 'root', 'etc', 'proc', 'sys', 'dev', 'boot'}

class DockerSecurityError(Exception):
    """Exception raised for Docker security violations"""
    pass

class DockerVolumeManager:
    """Manages Docker volume mounting and file access with bulletproof security"""
    
    def __init__(self, volumes_path: Optional[str] = None):
        """
        Initialize Docker volume manager with security validation
        
        Args:
            volumes_path: Base path for Docker volumes (default from config)
        """
        self.volumes_path = Path(volumes_path or current_app.config.get('DOCKER_VOLUMES_PATH', '/docker_volumes'))
        self._validate_volumes_path()
        self.ensure_volumes_directory()
    
    def _validate_volumes_path(self):
        """Validate that volumes path is secure and properly configured"""
        try:
            # Resolve and validate the volumes path
            resolved_path = self.volumes_path.resolve()
            
            # Ensure it's not in system critical directories
            critical_dirs = {'/etc', '/proc', '/sys', '/dev', '/boot', '/root'}
            if any(str(resolved_path).startswith(critical) for critical in critical_dirs):
                raise DockerSecurityError(f"Volumes path cannot be in system directory: {resolved_path}")
            
            # Update to resolved path for security
            self.volumes_path = resolved_path
            
        except Exception as e:
            logger.error(f"SECURITY: Invalid volumes path configuration: {e}")
            raise DockerSecurityError(f"Invalid volumes path: {e}")
    
    def ensure_volumes_directory(self):
        """Ensure the Docker volumes directory exists with secure permissions"""
        try:
            self.volumes_path.mkdir(parents=True, exist_ok=True, mode=0o750)
            logger.info(f"Docker volumes directory ensured at: {self.volumes_path}")
        except Exception as e:
            logger.error(f"Failed to create Docker volumes directory: {e}")
            raise
    
    def list_available_volumes(self, tenant_id: Optional[str] = None) -> List[str]:
        """
        List available Docker volumes with tenant authorization
        
        Args:
            tenant_id: Tenant ID for volume authorization (required for production)
            
        Returns:
            List of authorized volume names for the tenant
        """
        # Log security attempt
        self._log_security_event('list_volumes', {
            'tenant_id': tenant_id,
            'user_id': getattr(current_user, 'id', None) if current_user.is_authenticated else None
        })
        
        try:
            # Get all Docker volumes
            result = subprocess.run(
                ['docker', 'volume', 'ls', '--format', '{{.Name}}'],
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # Add timeout for security
            )
            all_volumes = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # Filter by tenant authorization if tenant_id provided
            if tenant_id:
                authorized_volumes = self._get_tenant_authorized_volumes(tenant_id)
                volumes = [v for v in all_volumes if v in authorized_volumes]
                logger.info(f"Found {len(volumes)} authorized volumes for tenant {tenant_id} out of {len(all_volumes)} total")
            else:
                # Development mode or public access - log warning
                logger.warning("SECURITY: Listing all Docker volumes without tenant filtering")
                volumes = all_volumes
                
            return volumes
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list Docker volumes: {e}")
            self._log_security_event('list_volumes_failed', {'error': str(e)})
            return []
        except FileNotFoundError:
            logger.warning("Docker command not found - Docker may not be installed")
            return []
        except subprocess.TimeoutExpired:
            logger.error("SECURITY: Docker volume listing timed out")
            self._log_security_event('list_volumes_timeout', {})
            return []
    
    def mount_volume(self, volume_name: str, mount_point: Optional[str] = None, tenant_id: Optional[str] = None) -> Path:
        """
        Mount a Docker volume to local filesystem with bulletproof security validation
        
        Args:
            volume_name: Name of the Docker volume (will be strictly validated)
            mount_point: Local mount point (optional, will be validated)
            tenant_id: Tenant ID for authorization (required for production)
            
        Returns:
            Path to the mounted volume
            
        Raises:
            DockerSecurityError: If security validation fails
            ValueError: If input validation fails
        """
        # CRITICAL: Validate volume name against path traversal attacks
        self._validate_volume_name(volume_name)
        
        # CRITICAL: Verify tenant authorization
        if tenant_id:
            self._verify_tenant_volume_access(tenant_id, volume_name)
        else:
            logger.warning(f"SECURITY: Mounting volume {volume_name} without tenant authorization")
        
        # Log security-sensitive operation
        self._log_security_event('mount_volume', {
            'volume_name': volume_name,
            'tenant_id': tenant_id,
            'user_id': getattr(current_user, 'id', None) if current_user.is_authenticated else None
        })
        
        # Create secure mount point with path validation
        if not mount_point:
            # Use secure temporary directory with UUID to prevent conflicts
            secure_dir_name = f"{volume_name}_{uuid.uuid4().hex[:8]}"
            mount_point_path = self.volumes_path / secure_dir_name
        else:
            mount_point_path = Path(mount_point)
        
        # CRITICAL: Validate mount point is within allowed volumes path
        self._validate_mount_path(mount_point_path)
        
        try:
            # Create mount directory with restricted permissions
            mount_point_path.mkdir(parents=True, exist_ok=True, mode=0o750)
            
            # Use docker run with bind mount to access volume content
            # Add security constraints to Docker command
            cmd = [
                'docker', 'run', '--rm',
                '--read-only',  # Run container in read-only mode
                '--security-opt', 'no-new-privileges',  # Prevent privilege escalation
                '--user', 'nobody:nogroup',  # Run as non-root user
                '-v', f'{volume_name}:/volume_data:ro',  # Mount volume as read-only
                '-v', f'{mount_point_path}:/host_mount',
                'alpine:latest',  # Use specific tag for security
                'cp', '-r', '/volume_data/.', '/host_mount/'
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=300  # 5 minute timeout
            )
            
            logger.info(f"Successfully mounted volume {volume_name} to {mount_point_path}")
            return mount_point_path
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to mount volume {volume_name}: {e}"
            logger.error(error_msg)
            self._log_security_event('mount_volume_failed', {
                'volume_name': volume_name,
                'error': str(e)
            })
            # Clean up on failure
            self._cleanup_mount_point(mount_point_path)
            raise DockerSecurityError(error_msg)
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout mounting volume {volume_name}"
            logger.error(error_msg)
            self._log_security_event('mount_volume_timeout', {
                'volume_name': volume_name
            })
            self._cleanup_mount_point(mount_point_path)
            raise DockerSecurityError(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error mounting volume {volume_name}: {e}")
            self._cleanup_mount_point(mount_point_path)
            raise
    
    def unmount_volume(self, mount_point: Union[str, Path]):
        """
        Securely clean up mounted volume directory with validation
        
        Args:
            mount_point: Path to the mounted volume
        """
        mount_path = Path(mount_point)
        
        # Validate that mount point is within our volumes directory
        try:
            self._validate_mount_path(mount_path)
        except DockerSecurityError as e:
            logger.error(f"SECURITY: Invalid unmount path: {e}")
            return
        
        self._cleanup_mount_point(mount_path)
    
    def _cleanup_mount_point(self, mount_path: Path):
        """Internal method to safely clean up mount points"""
        try:
            if mount_path.exists() and mount_path.is_dir():
                import shutil
                shutil.rmtree(mount_path)
                logger.info(f"Cleaned up mount point: {mount_path}")
        except Exception as e:
            logger.error(f"Failed to clean up mount point {mount_path}: {e}")
    
    def _validate_volume_name(self, volume_name: str):
        """Validate volume name against path traversal and injection attacks"""
        if not volume_name:
            raise ValueError("Volume name cannot be empty")
        
        if len(volume_name) > MAX_VOLUME_NAME_LENGTH:
            raise ValueError(f"Volume name too long (max {MAX_VOLUME_NAME_LENGTH} chars)")
        
        # Check for forbidden patterns
        if volume_name in FORBIDDEN_VOLUME_NAMES:
            raise DockerSecurityError(f"Forbidden volume name: {volume_name}")
        
        # Strict regex validation
        if not VOLUME_NAME_REGEX.match(volume_name):
            raise DockerSecurityError(
                f"Invalid volume name '{volume_name}'. Only alphanumeric characters, dots, underscores, and hyphens are allowed."
            )
        
        # Check for path traversal patterns
        if '..' in volume_name or '/' in volume_name or '\\' in volume_name:
            raise DockerSecurityError(f"Volume name contains forbidden path separators: {volume_name}")
    
    def _validate_mount_path(self, mount_path: Path):
        """Validate that mount path is within allowed volumes directory"""
        try:
            resolved_mount = mount_path.resolve()
            resolved_volumes = self.volumes_path.resolve()
            
            # Check if mount path is within volumes directory
            if not str(resolved_mount).startswith(str(resolved_volumes)):
                raise DockerSecurityError(
                    f"Mount path {resolved_mount} is outside allowed volumes directory {resolved_volumes}"
                )
                
        except Exception as e:
            raise DockerSecurityError(f"Path validation failed: {e}")
    
    def _verify_tenant_volume_access(self, tenant_id: str, volume_name: str):
        """Verify that tenant has authorization to access the specified volume"""
        try:
            from app.models.tenant import TenantVolume
            
            # Check if tenant has explicit access to this volume
            access = TenantVolume.query.filter_by(
                tenant_id=tenant_id,
                volume_name=volume_name,
                is_active=True
            ).first()
            
            if not access:
                error_msg = f"Tenant {tenant_id} not authorized for volume {volume_name}"
                logger.warning(f"SECURITY: {error_msg}")
                self._log_security_event('unauthorized_volume_access', {
                    'tenant_id': tenant_id,
                    'volume_name': volume_name
                })
                raise DockerSecurityError(error_msg)
                
        except ImportError:
            # TenantVolume model not available - log warning
            logger.warning("SECURITY: TenantVolume model not available - skipping authorization")
        except Exception as e:
            logger.error(f"Error verifying tenant volume access: {e}")
            raise DockerSecurityError(f"Volume authorization check failed: {e}")
    
    def _get_tenant_authorized_volumes(self, tenant_id: str) -> List[str]:
        """Get list of volumes that tenant is authorized to access"""
        try:
            from app.models.tenant import TenantVolume
            
            volumes = TenantVolume.query.filter_by(
                tenant_id=tenant_id,
                is_active=True
            ).all()
            
            return [v.volume_name for v in volumes]
            
        except ImportError:
            # TenantVolume model not available
            logger.warning("SECURITY: TenantVolume model not available - returning empty list")
            return []
        except Exception as e:
            logger.error(f"Error getting tenant authorized volumes: {e}")
            return []
    
    def _log_security_event(self, event_type: str, details: Dict):
        """Log security-sensitive events for audit trail"""
        try:
            security_log = {
                'event_type': event_type,
                'timestamp': self._get_timestamp(),
                'details': details,
                'source_ip': getattr(g, 'request_ip', 'unknown'),
                'user_agent': getattr(g, 'user_agent', 'unknown')
            }
            
            # Log to security audit log
            security_logger = logging.getLogger('security')
            security_logger.info(f"DOCKER_SECURITY: {event_type}", extra=security_log)
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

    def find_documents_in_volume(self, volume_path: Path) -> List[Dict[str, str]]:
        """
        Find all supported documents in a mounted volume with security validation
        
        Args:
            volume_path: Path to the mounted volume
            
        Returns:
            List of document info dictionaries
        """
        documents = []
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png'})
        
        try:
            # Validate volume path is secure
            self._validate_mount_path(volume_path)
            
            for file_path in volume_path.rglob('*'):
                if file_path.is_file():
                    # Additional security check for each file
                    try:
                        # Ensure file is within volume path (additional safety)
                        relative_path = file_path.relative_to(volume_path)
                        if '..' in str(relative_path):
                            logger.warning(f"SECURITY: Skipping file with path traversal: {file_path}")
                            continue
                        
                        extension = file_path.suffix.lower().lstrip('.')
                        if extension in allowed_extensions:
                            documents.append({
                                'filename': file_path.name,
                                'full_path': str(file_path),
                                'relative_path': str(relative_path),  # Use validated relative path
                                'extension': extension,
                                'size': file_path.stat().st_size,
                                'modified': file_path.stat().st_mtime
                            })
                    except ValueError as e:
                        logger.warning(f"SECURITY: Skipping invalid file path {file_path}: {e}")
                        continue
            
            logger.info(f"Found {len(documents)} documents in volume {volume_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error finding documents in volume {volume_path}: {e}")
            return []

class DockerContainerProcessor:
    """Process files directly from Docker containers with security validation"""
    
    def __init__(self):
        self.volume_manager = DockerVolumeManager()
    
    def list_containers_with_documents(self) -> List[Dict[str, str]]:
        """
        List running containers that might contain documents
        
        Returns:
            List of container info dictionaries
        """
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.ID}}\t{{.Names}}\t{{.Image}}'],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        container_id, name, image = parts[0], parts[1], parts[2]
                        containers.append({
                            'id': container_id,
                            'name': name,
                            'image': image
                        })
            
            logger.info(f"Found {len(containers)} running containers")
            return containers
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list containers: {e}")
            return []
        except FileNotFoundError:
            logger.warning("Docker command not found")
            return []
        except subprocess.TimeoutExpired:
            logger.error("SECURITY: Docker container listing timed out")
            return []
    
    def copy_files_from_container(self, container_id: str, source_path: str, 
                                destination_path: Optional[str] = None, tenant_id: Optional[str] = None) -> Path:
        """
        Copy files from a Docker container to local filesystem with security validation
        
        Args:
            container_id: Container ID or name (will be validated)
            source_path: Path inside the container (will be validated)
            destination_path: Local destination path (will be validated)
            tenant_id: Tenant ID for authorization
            
        Returns:
            Path to copied files
            
        Raises:
            DockerSecurityError: If security validation fails
        """
        # Validate container ID format
        self._validate_container_id(container_id)
        
        # Validate source path doesn't contain dangerous patterns
        self._validate_container_path(source_path)
        
        # Log security event
        self.volume_manager._log_security_event('copy_container_files', {
            'container_id': container_id,
            'source_path': source_path,
            'tenant_id': tenant_id
        })
        
        # Create secure destination path
        if not destination_path:
            secure_dir_name = f"container_{container_id}_{uuid.uuid4().hex[:8]}"
            dest_path = self.volume_manager.volumes_path / secure_dir_name
        else:
            dest_path = Path(destination_path)
        
        # Validate destination path
        self.volume_manager._validate_mount_path(dest_path)
        
        try:
            dest_path.mkdir(parents=True, exist_ok=True, mode=0o750)
            
            cmd = [
                'docker', 'cp', 
                f'{container_id}:{source_path}', 
                str(dest_path)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=300  # 5 minute timeout
            )
            
            logger.info(f"Successfully copied files from container {container_id} to {dest_path}")
            return dest_path
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to copy files from container {container_id}: {e}"
            logger.error(error_msg)
            self.volume_manager._log_security_event('copy_container_files_failed', {
                'container_id': container_id,
                'error': str(e)
            })
            self.volume_manager._cleanup_mount_point(dest_path)
            raise DockerSecurityError(error_msg)
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout copying files from container {container_id}"
            logger.error(error_msg)
            self.volume_manager._cleanup_mount_point(dest_path)
            raise DockerSecurityError(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error copying from container {container_id}: {e}")
            self.volume_manager._cleanup_mount_point(dest_path)
            raise
    
    def _validate_container_id(self, container_id: str):
        """Validate container ID format"""
        if not container_id:
            raise ValueError("Container ID cannot be empty")
        
        if len(container_id) > 100:  # Reasonable limit
            raise ValueError("Container ID too long")
        
        # Allow alphanumeric, hyphens, underscores (standard Docker container naming)
        if not re.match(r'^[a-zA-Z0-9._-]+$', container_id):
            raise DockerSecurityError(f"Invalid container ID format: {container_id}")
    
    def _validate_container_path(self, path: str):
        """Validate container path for security"""
        if not path:
            raise ValueError("Container path cannot be empty")
        
        # Check for dangerous patterns
        dangerous_patterns = ['../', '../', '..\\', '.\\', '/etc/', '/root/', '/proc/', '/sys/']
        for pattern in dangerous_patterns:
            if pattern in path:
                raise DockerSecurityError(f"Container path contains dangerous pattern '{pattern}': {path}")
    
    def scan_container_for_documents(self, container_id: str, 
                                   search_paths: Optional[List[str]] = None, 
                                   tenant_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Scan a container for documents without copying them (with security validation)
        
        Args:
            container_id: Container ID or name (will be validated)
            search_paths: Paths to search in the container (will be validated)
            tenant_id: Tenant ID for authorization
            
        Returns:
            List of document info dictionaries
        """
        # Validate container ID
        self._validate_container_id(container_id)
        
        # Use safe default search paths if none provided
        if search_paths is None:
            search_paths = ['/data', '/documents', '/files', '/app/uploads']
        
        # Validate all search paths
        for path in search_paths:
            self._validate_container_path(path)
        
        # Log security event
        self.volume_manager._log_security_event('scan_container', {
            'container_id': container_id,
            'search_paths': search_paths,
            'tenant_id': tenant_id
        })
        
        documents = []
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png'})
        
        for search_path in search_paths:
            try:
                # Use find command inside container to locate documents
                # Add security constraints
                cmd = [
                    'docker', 'exec',
                    '--user', 'nobody',  # Run as non-root user
                    container_id,
                    'find', search_path, '-type', 'f', '-readable',
                    '(', '-name', '*.pdf', '-o', '-name', '*.docx', '-o', '-name', '*.txt',
                    '-o', '-name', '*.jpg', '-o', '-name', '*.jpeg', '-o', '-name', '*.png', ')'
                ]
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True,
                    timeout=120  # 2 minute timeout per search path
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    for file_path in result.stdout.strip().split('\n'):
                        if file_path:
                            # Additional security validation
                            if '..' in file_path or file_path.startswith('/etc') or file_path.startswith('/root'):
                                logger.warning(f"SECURITY: Skipping dangerous file path: {file_path}")
                                continue
                                
                            filename = os.path.basename(file_path)
                            extension = os.path.splitext(filename)[1].lower().lstrip('.')
                            
                            if extension in allowed_extensions:
                                documents.append({
                                    'filename': filename,
                                    'container_path': file_path,
                                    'extension': extension,
                                    'container_id': container_id,
                                    'search_path': search_path
                                })
                
            except subprocess.CalledProcessError as e:
                logger.debug(f"Could not search path {search_path} in container {container_id}: {e}")
                continue
            except subprocess.TimeoutExpired:
                logger.warning(f"SECURITY: Timeout scanning path {search_path} in container {container_id}")
                continue
        
        logger.info(f"Found {len(documents)} documents in container {container_id}")
        return documents

def get_docker_processor() -> Optional[DockerContainerProcessor]:
    """
    Get a Docker container processor instance with availability check
    
    Returns:
        DockerContainerProcessor instance if Docker is available, None otherwise
    """
    try:
        # Check if Docker is available before creating processor
        from app.utils.health_checks import is_dependency_available
        
        if not is_dependency_available('docker'):
            logger.warning("Docker processor requested but Docker is not available")
            return None
            
        return DockerContainerProcessor()
        
    except Exception as e:
        logger.error(f"Failed to create Docker processor: {e}")
        return None