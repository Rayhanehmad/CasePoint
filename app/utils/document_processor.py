"""
Enhanced document processor for legal documents with OCR and Docker support
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

from flask import current_app
from app.utils.ocr_processor import get_ocr_processor, is_image_file
from app.utils.docker_processor import get_docker_processor
from app.utils.health_checks import get_health_manager
from app.models.legal import LegalDocument, DocumentType

logger = logging.getLogger(__name__)

class EnhancedDocumentProcessor:
    """Enhanced document processor with OCR and Docker support"""
    
    def __init__(self):
        self.supported_formats = {
            'pdf': self._process_pdf,
            'docx': self._process_docx,
            'txt': self._process_txt,
            'jpg': self._process_image,
            'jpeg': self._process_image,
            'png': self._process_image
        }
        self.ocr_processor = None
        self.docker_processor = None
    
    def _get_ocr_processor(self):
        """Get OCR processor instance (lazy loading)"""
        if self.ocr_processor is None:
            try:
                self.ocr_processor = get_ocr_processor()
            except Exception as e:
                logger.error(f"Failed to initialize OCR processor: {e}")
                self.ocr_processor = None  # Mark as failed
        return self.ocr_processor
    
    def _get_docker_processor(self):
        """Get Docker processor instance (lazy loading)"""
        if self.docker_processor is None:
            try:
                self.docker_processor = get_docker_processor()
            except Exception as e:
                logger.error(f"Failed to initialize Docker processor: {e}")
                self.docker_processor = None  # Mark as failed
        return self.docker_processor
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process PDF file using PyPDF2 with health checks"""
        health_manager = get_health_manager()
        if not health_manager.is_feature_available('pdf_processing'):
            error_response = health_manager.get_graceful_error_response('pdf_processing')
            return {
                'success': False,
                'error': error_response['error'],
                'extracted_text': '',
                'page_count': 0,
                'missing_dependencies': error_response.get('missing_dependencies', [])
            }
        
        try:
            extracted_text = []
            page_count = 0
            
            with open(file_path, 'rb') as file:
                if PyPDF2 is None:
                    raise ImportError("PyPDF2 is not available")
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            extracted_text.append(text)
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
            
            full_text = '\n\n'.join(extracted_text)
            
            return {
                'success': True,
                'extracted_text': full_text,
                'page_count': page_count,
                'word_count': len(full_text.split()) if full_text else 0,
                'processing_method': 'pypdf2'
            }
            
        except Exception as e:
            logger.error(f"PDF processing failed for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'extracted_text': '',
                'page_count': 0
            }
    
    def _process_docx(self, file_path: str) -> Dict[str, Any]:
        """Process DOCX file using python-docx with health checks"""
        health_manager = get_health_manager()
        if not health_manager.is_feature_available('docx_processing'):
            error_response = health_manager.get_graceful_error_response('docx_processing')
            return {
                'success': False,
                'error': error_response['error'],
                'extracted_text': '',
                'missing_dependencies': error_response.get('missing_dependencies', [])
            }
        
        try:
            if DocxDocument is None:
                raise ImportError("python-docx is not available")
            doc = DocxDocument(file_path)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            extracted_text = '\n\n'.join(paragraphs)
            
            return {
                'success': True,
                'extracted_text': extracted_text,
                'paragraph_count': len(paragraphs),
                'word_count': len(extracted_text.split()) if extracted_text else 0,
                'processing_method': 'python-docx'
            }
            
        except Exception as e:
            logger.error(f"DOCX processing failed for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'extracted_text': ''
            }
    
    def _process_txt(self, file_path: str) -> Dict[str, Any]:
        """Process plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                extracted_text = file.read()
            
            return {
                'success': True,
                'extracted_text': extracted_text,
                'word_count': len(extracted_text.split()) if extracted_text else 0,
                'processing_method': 'plain_text'
            }
            
        except Exception as e:
            logger.error(f"Text processing failed for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'extracted_text': ''
            }
    
    def _process_image(self, file_path: str) -> Dict[str, Any]:
        """Process image file using OCR with health checks"""
        health_manager = get_health_manager()
        if not health_manager.is_feature_available('ocr_processing'):
            error_response = health_manager.get_graceful_error_response('ocr_processing')
            return {
                'success': False,
                'error': error_response['error'],
                'extracted_text': '',
                'confidence': 0,
                'missing_dependencies': error_response.get('missing_dependencies', [])
            }
        
        ocr_processor = self._get_ocr_processor()
        if not ocr_processor:
            return {
                'success': False,
                'error': 'OCR processor initialization failed',
                'extracted_text': '',
                'confidence': 0
            }
        
        try:
            result = ocr_processor.extract_text_from_image(file_path, preprocess=True)
            
            # Enhance result with additional metadata
            result['processing_method'] = 'ocr_tesseract'
            result['file_type'] = 'image'
            
            return result
            
        except Exception as e:
            logger.error(f"Image OCR processing failed for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'extracted_text': '',
                'confidence': 0
            }
    
    def process_document(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a document file and extract text and metadata
        
        Args:
            file_path: Path to the document file
            filename: Original filename (optional)
            
        Returns:
            Dictionary containing processing results
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path_obj}")
            
            filename = filename or file_path_obj.name
            extension = file_path_obj.suffix.lower().lstrip('.')
            
            # Check if file type is supported
            if extension not in self.supported_formats:
                return {
                    'success': False,
                    'error': f'Unsupported file format: {extension}',
                    'supported_formats': list(self.supported_formats.keys())
                }
            
            # Calculate file metadata
            file_stat = file_path_obj.stat()
            file_size = file_stat.st_size
            file_hash = self.calculate_file_hash(str(file_path_obj))
            
            # Process file based on extension
            processor_func = self.supported_formats[extension]
            processing_result = processor_func(str(file_path))
            
            # Combine metadata with processing result
            result = {
                'filename': filename,
                'file_path': str(file_path_obj),
                'file_size': file_size,
                'file_hash': file_hash,
                'file_extension': extension,
                'processed_at': datetime.utcnow().isoformat(),
                **processing_result
            }
            
            # Determine document type based on content and filename
            result['document_type'] = self._determine_document_type(result)
            
            logger.info(f"Document processing completed for {filename}: "
                       f"{'success' if result['success'] else 'failed'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Document processing failed for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename or file_path
            }
    
    def _determine_document_type(self, processing_result: Dict[str, Any]) -> DocumentType:
        """
        Determine document type based on filename and content
        
        Args:
            processing_result: Result from document processing
            
        Returns:
            DocumentType enum value
        """
        filename = processing_result.get('filename', '').lower()
        extracted_text = processing_result.get('extracted_text', '').lower()
        
        # Keywords for different document types
        case_keywords = ['judgment', 'petitioner', 'respondent', 'court', 'case', 'appeal']
        statute_keywords = ['act', 'ordinance', 'section', 'clause', 'statute', 'law']
        contract_keywords = ['agreement', 'contract', 'party', 'whereas', 'covenant']
        
        # Check filename first
        if any(word in filename for word in ['judgment', 'case', 'appeal']):
            return DocumentType.JUDGMENT
        elif any(word in filename for word in ['act', 'ordinance', 'law']):
            return DocumentType.STATUTE
        elif any(word in filename for word in ['contract', 'agreement']):
            return DocumentType.CONTRACT
        
        # Check content
        case_score = sum(1 for keyword in case_keywords if keyword in extracted_text)
        statute_score = sum(1 for keyword in statute_keywords if keyword in extracted_text)
        contract_score = sum(1 for keyword in contract_keywords if keyword in extracted_text)
        
        if case_score >= 2:
            return DocumentType.CASE_LAW
        elif statute_score >= 2:
            return DocumentType.STATUTE
        elif contract_score >= 2:
            return DocumentType.CONTRACT
        
        # Default fallback
        return DocumentType.LEGAL_OPINION
    
    def process_docker_volume_documents(self, volume_name: str) -> List[Dict[str, Any]]:
        """
        Process all documents from a Docker volume
        
        Args:
            volume_name: Name of the Docker volume
            
        Returns:
            List of processing results
        """
        docker_processor = self._get_docker_processor()
        if not docker_processor:
            logger.error("Docker processor not available")
            return []
        
        try:
            # Mount the volume
            mount_path = docker_processor.volume_manager.mount_volume(volume_name)
            
            # Find documents in the mounted volume
            documents = docker_processor.volume_manager.find_documents_in_volume(mount_path)
            
            # Process each document
            results = []
            for doc_info in documents:
                try:
                    result = self.process_document(doc_info['full_path'], doc_info['filename'])
                    result['source'] = 'docker_volume'
                    result['volume_name'] = volume_name
                    result['original_path'] = doc_info['relative_path']
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process document {doc_info['filename']}: {e}")
                    results.append({
                        'filename': doc_info['filename'],
                        'success': False,
                        'error': str(e),
                        'source': 'docker_volume',
                        'volume_name': volume_name
                    })
            
            # Clean up mounted volume
            docker_processor.volume_manager.unmount_volume(mount_path)
            
            logger.info(f"Processed {len(results)} documents from Docker volume {volume_name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to process Docker volume {volume_name}: {e}")
            return []
    
    def process_container_documents(self, container_id: str, 
                                  source_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Process documents from a Docker container
        
        Args:
            container_id: Container ID or name
            source_paths: Paths to search in the container
            
        Returns:
            List of processing results
        """
        docker_processor = self._get_docker_processor()
        if not docker_processor:
            logger.error("Docker processor not available")
            return []
        
        try:
            # Scan container for documents
            documents = docker_processor.scan_container_for_documents(container_id, source_paths)
            
            results = []
            for doc_info in documents:
                try:
                    # Copy file from container to temporary location
                    temp_path = docker_processor.copy_files_from_container(
                        container_id, 
                        doc_info['container_path']
                    )
                    
                    # Process the copied file
                    copied_file_path = temp_path / doc_info['filename']
                    if copied_file_path.exists():
                        result = self.process_document(str(copied_file_path), doc_info['filename'])
                        result['source'] = 'docker_container'
                        result['container_id'] = container_id
                        result['original_container_path'] = doc_info['container_path']
                        results.append(result)
                    
                except Exception as e:
                    logger.error(f"Failed to process container document {doc_info['filename']}: {e}")
                    results.append({
                        'filename': doc_info['filename'],
                        'success': False,
                        'error': str(e),
                        'source': 'docker_container',
                        'container_id': container_id
                    })
            
            logger.info(f"Processed {len(results)} documents from container {container_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to process container {container_id}: {e}")
            return []

def get_document_processor() -> EnhancedDocumentProcessor:
    """
    Get an enhanced document processor instance
    
    Returns:
        EnhancedDocumentProcessor instance
    """
    return EnhancedDocumentProcessor()

def process_file_for_legal_document(file_path: str, 
                                  legal_document: LegalDocument) -> Dict[str, Any]:
    """
    Process a file and update a LegalDocument instance
    
    Args:
        file_path: Path to the file to process
        legal_document: LegalDocument instance to update
        
    Returns:
        Processing result dictionary
    """
    processor = get_document_processor()
    result = processor.process_document(file_path, legal_document.original_filename)
    
    if result['success']:
        # Update legal document with extracted information
        legal_document.extracted_text = result.get('extracted_text', '')
        legal_document.file_hash = result.get('file_hash')
        legal_document.processing_status = 'completed'
        
        # Set confidence based on processing method
        if result.get('processing_method') == 'ocr_tesseract':
            legal_document.extraction_confidence = result.get('confidence', 0) / 100
        else:
            # For non-OCR methods, set high confidence
            legal_document.extraction_confidence = 0.95
        
        # Store additional metadata
        legal_document.custom_metadata = {
            'processing_method': result.get('processing_method'),
            'word_count': result.get('word_count', 0),
            'page_count': result.get('page_count'),
            'processed_at': result.get('processed_at')
        }
        
        # Update document type if determined
        if 'document_type' in result:
            legal_document.document_type = result['document_type']
    
    else:
        legal_document.processing_status = 'failed'
        legal_document.custom_metadata = {
            'error': result.get('error'),
            'processed_at': result.get('processed_at')
        }
    
    return result