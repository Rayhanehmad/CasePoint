"""
Multi-Citation PDF Upload Route
Handles bulk PDF upload with automatic citation detection and splitting.
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime

from models import db
from models.case import LegalCitation
from utils.extract_text import extract_text_from_pdf
from utils.citation_detect import detect_headings, validate_heading_quality
from utils.pdf_slice import slice_pdf_by_range
from utils.metadata import extract_court_from_citation, extract_parties, normalize_citation

# Create blueprint
upload_multi_pdf_bp = Blueprint('upload_multi_pdf', __name__)

logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE = 300 * 1024 * 1024  # 300 MB
MAX_PAGES = 500
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_multi_pdf_bp.route('/api/upload_multi_pdf', methods=['POST'])
def upload_multi_pdf():
    """
    Upload and process multi-citation PDF.
    
    Form data:
        file: PDF file (multipart/form-data)
        
    Query params:
        dry_run: If '1', only detect citations without creating records
        
    Returns:
        JSON with detection results and created citation IDs
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Empty filename'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Only PDF files are allowed'
            }), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'File size exceeds {MAX_FILE_SIZE / (1024*1024):.0f}MB limit'
            }), 400
        
        # Dry run mode
        dry_run = request.args.get('dry_run') == '1'
        
        # Save source file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        
        source_dir = os.path.join(current_app.root_path, '..', 'uploads', 'source')
        os.makedirs(source_dir, exist_ok=True)
        
        source_path = os.path.join(source_dir, safe_filename)
        file.save(source_path)
        
        logger.info(f"Saved source PDF: {source_path} ({file_size / (1024*1024):.2f} MB)")
        
        # Step 1: Extract text
        logger.info("Extracting text from PDF...")
        full_text, page_texts, used_ocr = extract_text_from_pdf(source_path, use_ocr_fallback=True)
        
        num_pages = len(page_texts)
        
        if num_pages > MAX_PAGES:
            return jsonify({
                'success': False,
                'error': f'PDF has {num_pages} pages, exceeding {MAX_PAGES} page limit'
            }), 400
        
        logger.info(f"Extracted {num_pages} pages, OCR used: {used_ocr}")
        
        # Step 2: Detect citations
        logger.info("Detecting citations...")
        headings = detect_headings(full_text, page_texts)
        
        # Validate headings
        is_valid, warning = validate_heading_quality(headings)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': warning,
                'total_detected': 0
            }), 400
        
        logger.info(f"Detected {len(headings)} citations")
        
        # If dry run, return detection results without processing
        if dry_run:
            return jsonify({
                'success': True,
                'dry_run': True,
                'total_detected': len(headings),
                'used_ocr': used_ocr,
                'num_pages': num_pages,
                'citations': [{
                    'citation': h['citation'],
                    'journal': h['journal'],
                    'year': h['year'],
                    'page_range': f"{h['page_range_start'] + 1}-{h['page_range_end']}"
                } for h in headings]
            }), 200
        
        # Step 3: Process each citation
        created_ids = []
        warnings = []
        
        citations_dir = os.path.join(current_app.root_path, '..', 'uploads', 'citations')
        
        for i, heading in enumerate(headings):
            try:
                citation_text = heading['citation']
                journal = heading['journal']
                year = heading['year']
                page_start = heading['page_range_start']
                page_end = heading['page_range_end']
                
                logger.info(f"Processing citation {i+1}/{len(headings)}: {citation_text}")
                
                # Normalize citation
                normalized_citation = normalize_citation(citation_text)
                
                # Check if citation already exists
                existing = LegalCitation.query.filter(
                    db.func.lower(LegalCitation.citation) == normalized_citation.lower()
                ).first()
                
                if existing:
                    warnings.append(f"Citation already exists: {normalized_citation} (ID: {existing.id})")
                    continue
                
                # Extract full text for this citation
                citation_full_text = "\n\n".join(page_texts[page_start:page_end])
                
                # Extract metadata
                court = extract_court_from_citation(citation_text, citation_full_text)
                parties = extract_parties(citation_full_text, journal)
                
                # Slice PDF
                pdf_path = slice_pdf_by_range(
                    source_pdf_path=source_path,
                    page_start=page_start,
                    page_end=page_end,
                    output_dir=citations_dir,
                    citation=citation_text,
                    journal=journal,
                    year=year
                )
                
                if not pdf_path:
                    warnings.append(f"Failed to slice PDF for citation: {normalized_citation}")
                    continue
                
                # Create LegalCitation record
                new_citation = LegalCitation(
                    document_type='case',
                    title=parties or normalized_citation,
                    citation=normalized_citation,
                    court=court,
                    year=year,
                    journal=journal,
                    summary="",
                    full_text=citation_full_text,
                    pdf_path=pdf_path,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(new_citation)
                db.session.flush()  # Get ID without committing
                
                created_ids.append(new_citation.id)
                
                logger.info(f"Created citation ID {new_citation.id}: {normalized_citation}")
                
            except Exception as e:
                logger.error(f"Error processing citation {heading['citation']}: {str(e)}")
                warnings.append(f"Failed to process {heading['citation']}: {str(e)}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"Successfully created {len(created_ids)} citations from {num_pages} pages")
        
        return jsonify({
            'success': True,
            'total_detected': len(headings),
            'total_created': len(created_ids),
            'created_ids': created_ids,
            'warnings': warnings,
            'used_ocr': used_ocr,
            'num_pages': num_pages,
            'source_file': safe_filename
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Upload multi-PDF failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
