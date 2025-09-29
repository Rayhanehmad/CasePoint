"""
OCR service for document text extraction
"""

import os
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from typing import Tuple, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class OCRService:
    """OCR service for extracting text from documents"""
    
    def __init__(self):
        # Configure tesseract path if specified
        if settings.TESSERACT_PATH and os.path.exists(settings.TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
    
    async def extract_text_from_file(self, file_path: str, file_type: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract text from file with confidence score"""
        
        try:
            if file_type.lower() == 'pdf':
                return await self._extract_from_pdf(file_path)
            elif file_type.lower() in ['jpg', 'jpeg', 'png']:
                return await self._extract_from_image(file_path)
            elif file_type.lower() == 'txt':
                return await self._extract_from_txt(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return None, None
                
        except Exception as e:
            logger.error(f"OCR extraction failed for {file_path}: {str(e)}")
            return None, None
    
    async def _extract_from_pdf(self, file_path: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract text from PDF file"""
        
        try:
            doc = fitz.open(file_path)
            text_content = []
            total_confidence = 0
            page_count = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # First try to extract text directly (for text-based PDFs)
                text = page.get_text()
                
                if text.strip():
                    text_content.append(text)
                    total_confidence += 100  # Direct text extraction has 100% confidence
                    page_count += 1
                else:
                    # If no text found, try OCR on rendered page image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img_data = pix.tobytes("png")
                    
                    # Save temporary image for OCR
                    temp_img_path = f"/tmp/page_{page_num}.png"
                    with open(temp_img_path, "wb") as f:
                        f.write(img_data)
                    
                    # Perform OCR
                    ocr_text, confidence = await self._extract_from_image(temp_img_path)
                    if ocr_text:
                        text_content.append(ocr_text)
                        total_confidence += confidence or 0
                        page_count += 1
                    
                    # Clean up temp file
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
            
            doc.close()
            
            if text_content:
                combined_text = "\n\n".join(text_content)
                avg_confidence = total_confidence / page_count if page_count > 0 else 0
                return combined_text, avg_confidence
            
            return None, None
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            return None, None
    
    async def _extract_from_image(self, file_path: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract text from image file using OCR"""
        
        try:
            # Open image
            image = Image.open(file_path)
            
            # Preprocess image for better OCR
            image = image.convert('RGB')
            
            # Configure OCR with multiple languages
            config = f"--oem 3 --psm 6 -l {'+'.join(settings.OCR_LANGUAGES)}"
            
            # Extract text with confidence
            data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
            
            # Filter out low confidence words and combine text
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > 30:  # Only include words with confidence > 30
                    word = data['text'][i].strip()
                    if word:
                        text_parts.append(word)
                        confidences.append(int(conf))
            
            if text_parts:
                extracted_text = ' '.join(text_parts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                return extracted_text, avg_confidence
            
            return None, None
            
        except Exception as e:
            logger.error(f"Image OCR failed: {str(e)}")
            return None, None
    
    async def _extract_from_txt(self, file_path: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract text from plain text file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content, 100.0  # Plain text has 100% confidence
            
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                return content, 100.0
            except Exception as e:
                logger.error(f"Text file reading failed: {str(e)}")
                return None, None
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return None, None