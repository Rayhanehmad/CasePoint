"""
Bulk document processor with AI-powered metadata extraction
"""

import os
import logging
from openai import OpenAI
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
import json
import re
from datetime import datetime
from services.utils import extract_journal_from_citation, extract_court_from_citation

logger = logging.getLogger(__name__)

class BulkDocumentProcessor:
    def __init__(self):
        self._client = None
    
    def get_client(self):
        """Get or create OpenAI client"""
        if self._client is None and os.environ.get('OPENAI_API_KEY'):
            self._client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        return self._client
    
    def extract_text_from_file(self, file_path, file_type):
        """Extract text from various file formats"""
        try:
            if file_type == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_type in ['docx', 'doc']:
                return self._extract_from_docx(file_path)
            elif file_type == 'txt':
                return self._extract_from_txt(file_path)
            elif file_type in ['jpg', 'jpeg', 'png', 'tiff']:
                return self._extract_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF"""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    
    def _extract_from_docx(self, file_path):
        """Extract text from DOCX file using shared utility"""
        from services.utils_docx_extractor import extract_text_from_docx
        return extract_text_from_docx(file_path)
    
    def _extract_from_txt(self, file_path):
        """Extract text from TXT"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()
    
    def _extract_from_image(self, file_path):
        """Extract text from image using pytesseract OCR"""
        try:
            # Use pytesseract for OCR (simpler than OpenAI Vision)
            from PIL import Image
            import pytesseract
            
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting from image: {str(e)}")
            raise
    
    def extract_legal_metadata(self, text):
        """Use OpenAI to extract legal metadata from text"""
        try:
            prompt = """You are a legal document analyzer for Pakistan law. Extract the following metadata from the provided legal document text:

1. citation - Official citation (e.g., "PLD 1984 SC 191", "2020 SCMR 1234")
2. title - Case title (e.g., "Imtiaz Ahmed v. The State")
3. court - Court name (e.g., "Supreme Court of Pakistan", "Lahore High Court")
4. jurisdiction - Jurisdiction (e.g., "Federal", "Punjab", "Sindh")
5. date_decided - Decision date in YYYY-MM-DD format
6. year - Year of decision
7. legal_area - Legal area (e.g., "Criminal Law", "Civil Law", "Constitutional Law", "Tax Law", "Family Law")
8. case_type - Case type (e.g., "Appeal", "Writ Petition", "Review", "Criminal Appeal")
9. judges - Comma-separated list of judges
10. summary - Brief 2-3 sentence summary of the case
11. keywords - Comma-separated relevant legal keywords
12. headnotes - Legal headnotes/principles (if available)

Return a valid JSON object with these fields. If a field cannot be determined, use null. Be accurate and extract only what's clearly stated in the document.

Document text:
---
""" + text[:8000]  # Limit to first 8000 chars to save tokens

            client = self.get_client()
            if not client:
                raise Exception("OpenAI API key not configured")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a legal document metadata extractor. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            metadata_json = response.choices[0].message.content
            metadata = json.loads(metadata_json)
            
            # Clean and validate
            if metadata.get('date_decided'):
                try:
                    # Validate date format
                    datetime.strptime(metadata['date_decided'], '%Y-%m-%d')
                except ValueError:
                    metadata['date_decided'] = None
            
            if metadata.get('year'):
                try:
                    metadata['year'] = int(metadata['year'])
                except (ValueError, TypeError):
                    metadata['year'] = None
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata with AI: {str(e)}")
            raise
    
    def process_document(self, file_path, filename, uploaded_by_user_id):
        """Process a single document and return citation data"""
        try:
            # Determine file type
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            # Extract text
            logger.info(f"Extracting text from {filename}")
            full_text = self.extract_text_from_file(file_path, file_ext)
            
            if not full_text or len(full_text) < 50:
                return {
                    'success': False,
                    'message': 'Insufficient text extracted from document'
                }
            
            # Extract metadata using AI
            logger.info(f"Extracting metadata from {filename}")
            metadata = self.extract_legal_metadata(full_text)
            
            # Validate required fields
            if not metadata.get('citation'):
                return {
                    'success': False,
                    'message': 'Could not extract citation from document'
                }
            
            if not metadata.get('title'):
                return {
                    'success': False,
                    'message': 'Could not extract case title from document'
                }
            
            # Auto-extract court if not provided by AI
            citation_text = metadata.get('citation')
            court_value = metadata.get('court')
            if not court_value and citation_text:
                court_value = extract_court_from_citation(citation_text, full_text)
            
            # Prepare citation data
            citation_data = {
                'document_type': 'case',
                'title': metadata.get('title'),
                'citation': citation_text,
                'court': court_value,
                'jurisdiction': metadata.get('jurisdiction'),
                'date_decided': datetime.strptime(metadata['date_decided'], '%Y-%m-%d').date() if metadata.get('date_decided') else None,
                'year': metadata.get('year'),
                'journal': extract_journal_from_citation(citation_text),
                'legal_area': metadata.get('legal_area'),
                'case_type': metadata.get('case_type'),
                'judges': metadata.get('judges'),
                'summary': metadata.get('summary'),
                'full_text': full_text,
                'headnotes': metadata.get('headnotes'),
                'keywords': metadata.get('keywords'),
                'file_path': file_path,
                'file_type': file_ext,
                'uploaded_by': uploaded_by_user_id
            }
            
            return {
                'success': True,
                'data': citation_data,
                'citation': metadata.get('citation'),
                'message': f'Successfully extracted: {metadata.get("citation")}'
            }
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }


# Global instance
bulk_processor = BulkDocumentProcessor()
