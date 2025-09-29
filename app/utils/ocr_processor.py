"""
OCR text extraction utilities for image files using pytesseract
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image, ImageEnhance, ImageFilter
from PIL.Image import Resampling
import pytesseract
from flask import current_app
from app.utils.health_checks import get_health_manager

logger = logging.getLogger(__name__)

class OCRProcessor:
    """OCR processor for extracting text from images"""
    
    def __init__(self, language: str = 'eng', config: str = '--psm 6'):
        """
        Initialize OCR processor
        
        Args:
            language: Tesseract language code (default: 'eng')
            config: Tesseract configuration string
        """
        self.language = language
        self.config = config
        self.supported_formats = {'jpg', 'jpeg', 'png', 'tiff', 'bmp', 'gif'}
        
        # Verify tesseract installation
        self._verify_tesseract()
    
    def _verify_tesseract(self):
        """Verify that tesseract is properly installed using health checks"""
        health_manager = get_health_manager()
        tesseract_status = health_manager.check_tesseract()
        pytesseract_status = health_manager.check_pytesseract()
        
        if not tesseract_status['available']:
            error_msg = f"Tesseract binary not available: {tesseract_status.get('error', 'Unknown error')}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        if not pytesseract_status['available']:
            error_msg = f"pytesseract not available: {pytesseract_status.get('error', 'Unknown error')}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info(f"OCR system ready - Tesseract: {tesseract_status.get('version', 'unknown')}, pytesseract available")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed image
        """
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Apply median filter to reduce noise
            image = image.filter(ImageFilter.MedianFilter())
            
            # Resize if image is too small (minimum 300 DPI equivalent)
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000 / width, 1000 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Resampling.LANCZOS)
                logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
            return image
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image  # Return original if preprocessing fails
    
    def extract_text_from_image(self, image_path: str, 
                              preprocess: bool = True) -> Dict[str, Any]:
        """
        Extract text from an image file
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to preprocess the image
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            image_path_obj = Path(image_path)
            
            if not image_path_obj.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Check if file extension is supported
            extension = image_path_obj.suffix.lower().lstrip('.')
            if extension not in self.supported_formats:
                raise ValueError(f"Unsupported image format: {extension}")
            
            # Open and preprocess image
            with Image.open(image_path_obj) as image:
                if preprocess:
                    image = self.preprocess_image(image)
                
                # Extract text using pytesseract
                extracted_text = pytesseract.image_to_string(
                    image, 
                    lang=self.language, 
                    config=self.config
                ).strip()
                
                # Get confidence scores for each word
                data = pytesseract.image_to_data(
                    image, 
                    lang=self.language, 
                    config=self.config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                # Extract words with high confidence
                high_confidence_words = []
                for i, conf in enumerate(data['conf']):
                    if int(conf) > 60:  # Only words with >60% confidence
                        word = data['text'][i].strip()
                        if word:
                            high_confidence_words.append({
                                'word': word,
                                'confidence': int(conf),
                                'x': data['left'][i],
                                'y': data['top'][i],
                                'width': data['width'][i],
                                'height': data['height'][i]
                            })
                
                result = {
                    'extracted_text': extracted_text,
                    'confidence': avg_confidence,
                    'word_count': len(extracted_text.split()) if extracted_text else 0,
                    'char_count': len(extracted_text) if extracted_text else 0,
                    'high_confidence_words': high_confidence_words,
                    'language': self.language,
                    'preprocessed': preprocess,
                    'image_dimensions': image.size,
                    'success': True
                }
                
                logger.info(f"OCR completed for {image_path_obj.name}: "
                          f"{result['word_count']} words, "
                          f"{result['confidence']:.1f}% avg confidence")
                
                return result
                
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            return {
                'extracted_text': '',
                'confidence': 0,
                'word_count': 0,
                'char_count': 0,
                'high_confidence_words': [],
                'language': self.language,
                'preprocessed': preprocess,
                'error': str(e),
                'success': False
            }
    
    def extract_text_from_multiple_images(self, image_paths: List[str], 
                                        preprocess: bool = True) -> List[Dict[str, Any]]:
        """
        Extract text from multiple image files
        
        Args:
            image_paths: List of paths to image files
            preprocess: Whether to preprocess images
            
        Returns:
            List of OCR results for each image
        """
        results = []
        
        for image_path in image_paths:
            result = self.extract_text_from_image(image_path, preprocess)
            result['file_path'] = str(image_path)
            result['filename'] = Path(image_path).name
            results.append(result)
        
        successful = sum(1 for r in results if r['success'])
        logger.info(f"OCR completed for {len(image_paths)} images: "
                   f"{successful} successful, {len(image_paths) - successful} failed")
        
        return results
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of available Tesseract languages
        
        Returns:
            List of language codes
        """
        try:
            langs = pytesseract.get_languages(config='')
            logger.info(f"Available OCR languages: {langs}")
            return langs
        except Exception as e:
            logger.error(f"Could not get available languages: {e}")
            return ['eng']  # Return default
    
    def detect_language(self, image_path: str) -> Dict[str, Any]:
        """
        Detect the language of text in an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with detected languages and confidence scores
        """
        try:
            with Image.open(image_path) as image:
                # Use orientation and script detection
                osd = pytesseract.image_to_osd(image)
                
                # Parse OSD output
                lines = osd.split('\n')
                result = {}
                
                for line in lines:
                    if 'Script:' in line:
                        result['script'] = line.split(':')[1].strip()
                    elif 'Orientation' in line and 'degrees' in line:
                        result['orientation'] = line
                
                logger.info(f"Language detection completed for {Path(image_path).name}")
                return result
                
        except Exception as e:
            logger.error(f"Language detection failed for {image_path}: {e}")
            return {'error': str(e)}

def get_ocr_processor(language: Optional[str] = None, config: Optional[str] = None) -> Optional[OCRProcessor]:
    """
    Get an OCR processor instance with app configuration and health checks
    
    Args:
        language: Override language (default from config)
        config: Override config (default from config)
        
    Returns:
        OCRProcessor instance or None if OCR is not available
    """
    # Check if OCR feature is available
    health_manager = get_health_manager()
    if not health_manager.is_feature_available('ocr_processing'):
        logger.warning("OCR processing not available - missing dependencies")
        return None
    
    try:
        if language is None:
            language = current_app.config.get('OCR_LANGUAGE', 'eng')
        if config is None:
            config = current_app.config.get('OCR_CONFIG', '--psm 6')
        
        # Ensure we have valid string values
        language = language or 'eng'
        config = config or '--psm 6'
        
        return OCRProcessor(language=language, config=config)
    except RuntimeError as e:
        logger.error(f"Failed to initialize OCR processor: {e}")
        return None

def is_image_file(filename: str) -> bool:
    """
    Check if a file is a supported image format
    
    Args:
        filename: Name of the file
        
    Returns:
        True if the file is a supported image format
    """
    extension = Path(filename).suffix.lower().lstrip('.')
    supported_formats = {'jpg', 'jpeg', 'png', 'tiff', 'bmp', 'gif'}
    return extension in supported_formats