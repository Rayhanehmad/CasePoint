"""
Admin routes - Upload citations, bulk CSV upload, admin panel
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from models import db
from models.user import User
from models.case import LegalCitation
from services import ocr_service, vector_search
from services.citation_extractor import citation_extractor
from services.bulk_processor import bulk_processor
from routes.auth_routes import admin_required
import os
import logging
import csv
import io
from datetime import datetime

admin_bp = Blueprint('admin_api', __name__)  # Changed from 'admin' to 'admin_api' to avoid conflict with Flask-Admin


def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp', 'docx', 'doc', 'txt', 'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin_bp.route('/panel')
@admin_required
def admin_panel():
    """Admin dashboard"""
    # Get statistics
    total_cases = LegalCitation.query.filter_by(document_type='case').count()
    total_acts = LegalCitation.query.filter(
        LegalCitation.document_type.in_(['act', 'statute'])
    ).count()
    total_rules = LegalCitation.query.filter_by(document_type='rule').count()
    total_users = User.query.count()
    
    # Recent uploads
    recent_uploads = LegalCitation.query.order_by(
        LegalCitation.created_at.desc()
    ).limit(10).all()
    
    breadcrumbs = [{'text': 'Admin Panel', 'url': url_for('admin_api.admin_panel')}]
    
    return render_template('admin_panel.html',
                         total_cases=total_cases,
                         total_acts=total_acts,
                         total_rules=total_rules,
                         total_users=total_users,
                         recent_uploads=recent_uploads,
                         breadcrumbs=breadcrumbs)


@admin_bp.route('/upload-citation', methods=['GET', 'POST'])
@admin_required
def upload_citation():
    """Upload single citation to database"""
    if request.method == 'POST':
        try:
            # Extract form data
            citation_data = {
                'document_type': request.form.get('document_type', 'case'),
                'title': request.form.get('title'),
                'citation': request.form.get('citation'),
                'court': request.form.get('court'),
                'jurisdiction': request.form.get('jurisdiction'),
                'date_decided': datetime.strptime(request.form.get('date_decided'), '%Y-%m-%d').date() if request.form.get('date_decided') else None,
                'year': int(request.form.get('year')) if request.form.get('year') else None,
                'legal_area': request.form.get('legal_area'),
                'case_type': request.form.get('case_type'),
                'judges': request.form.get('judges'),
                'summary': request.form.get('summary'),
                'full_text': request.form.get('full_text'),
                'headnotes': request.form.get('headnotes'),
                'keywords': request.form.get('keywords'),
                'citations_referred': request.form.get('citations_referred'),
                'statutes_referred': request.form.get('statutes_referred'),
                'uploaded_by': session['user_id']
            }
            
            # Create new citation
            citation = LegalCitation(**citation_data)
            db.session.add(citation)
            db.session.commit()
            
            # Add to vector database if full_text exists
            if citation.full_text:
                metadata = {
                    'title': citation.title,
                    'citation': citation.citation,
                    'court': citation.court,
                    'year': citation.year,
                    'legal_area': citation.legal_area,
                    'document_type': citation.document_type
                }
                success = vector_search.add_document_to_vector_db(str(citation.id), citation.full_text, metadata)
                if success:
                    citation.vector_id = str(citation.id)
                    db.session.commit()
            
            flash(f'Citation {citation.citation} uploaded successfully!', 'success')
            return redirect(url_for('admin_api.upload_citation'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading citation: {str(e)}', 'error')
            return redirect(url_for('admin_api.upload_citation'))
    
    return render_template('upload_citation.html')


@admin_bp.route('/upload-file', methods=['POST'])
@admin_required
def upload_file():
    """Upload citation document file with OCR extraction"""
    
    if 'file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('admin_api.upload_citation'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin_api.upload_citation'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Get file extension
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        # Extract text using OCR
        extracted_text, ocr_confidence = ocr_service.extract_text_from_file(filepath, file_ext)
        
        if extracted_text:
            # Extract metadata from document text
            metadata = citation_extractor.extract_metadata(extracted_text, filename)
            
            # Get citation string
            extracted_citation = request.form.get('citation') or metadata.get('citation')
            
            # Check if citation already exists in database
            existing_citation = LegalCitation.query.filter_by(citation=extracted_citation).first()
            
            if existing_citation:
                flash(f'Citation "{extracted_citation}" already exists in database! Please use a different document or update the existing record.', 'warning')
                return redirect(url_for('admin_api.upload_citation'))
            
            # Store document with extracted metadata
            citation_data = {
                'document_type': request.form.get('document_type', 'case'),
                'title': request.form.get('title') or metadata.get('title') or filename.rsplit('.', 1)[0],
                'citation': extracted_citation,
                'court': request.form.get('court') or metadata.get('court') or '',
                'jurisdiction': request.form.get('jurisdiction') or metadata.get('jurisdiction') or '',
                'year': int(request.form.get('year')) if request.form.get('year') else metadata.get('year'),
                'legal_area': request.form.get('legal_area') or metadata.get('legal_area') or '',
                'judges': metadata.get('judges'),
                'summary': request.form.get('summary') or metadata.get('summary') or '',
                'headnotes': metadata.get('headnotes'),
                'file_path': filepath,
                'file_type': file_ext,
                'full_text': extracted_text,
                'ocr_confidence': ocr_confidence,
                'uploaded_by': session['user_id']
            }
            
            citation = LegalCitation(**citation_data)
            db.session.add(citation)
            db.session.commit()
            
            # Add to vector database
            vector_metadata = {
                'title': citation.title,
                'citation': citation.citation,
                'court': citation.court,
                'year': citation.year,
                'legal_area': citation.legal_area,
                'document_type': citation.document_type
            }
            success = vector_search.add_document_to_vector_db(str(citation.id), extracted_text, vector_metadata)
            if success:
                citation.vector_id = str(citation.id)
                db.session.commit()
            
            flash(f'Document uploaded successfully! Citation: {extracted_citation} | Confidence: {ocr_confidence:.1f}%', 'success')
        else:
            flash('Could not extract text from document', 'error')
        
        return redirect(url_for('admin_api.upload_citation'))
    
    flash('File type not allowed', 'error')
    return redirect(url_for('admin_api.upload_citation'))


@admin_bp.route('/bulk-upload-csv', methods=['POST'])
@admin_required
def bulk_upload_csv():
    """Bulk upload citations from CSV file"""
    
    if 'csv_file' not in request.files:
        flash('No CSV file provided', 'error')
        return redirect(url_for('admin_api.admin_panel'))
    
    file = request.files['csv_file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin_api.admin_panel'))
    
    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('admin_api.admin_panel'))
    
    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Check if citation already exists
                existing = LegalCitation.query.filter_by(citation=row.get('citation')).first()
                if existing:
                    error_count += 1
                    errors.append(f"Row {row_num}: Citation '{row.get('citation')}' already exists")
                    continue
                
                # Parse year
                year = None
                if row.get('year'):
                    try:
                        year = int(row.get('year'))
                    except ValueError:
                        pass
                
                # Parse date
                date_decided = None
                if row.get('date_decided'):
                    try:
                        date_decided = datetime.strptime(row.get('date_decided'), '%Y-%m-%d').date()
                    except ValueError:
                        pass
                
                # Create citation
                citation_data = {
                    'document_type': row.get('document_type', 'case').lower(),
                    'title': row.get('title', ''),
                    'citation': row.get('citation', ''),
                    'court': row.get('court', ''),
                    'jurisdiction': row.get('jurisdiction', ''),
                    'date_decided': date_decided,
                    'year': year,
                    'legal_area': row.get('legal_area', ''),
                    'case_type': row.get('case_type', ''),
                    'judges': row.get('judges', ''),
                    'summary': row.get('summary', ''),
                    'full_text': row.get('full_text', ''),
                    'headnotes': row.get('headnotes', ''),
                    'keywords': row.get('keywords', ''),
                    'citations_referred': row.get('citations_referred', ''),
                    'statutes_referred': row.get('statutes_referred', ''),
                    'uploaded_by': session['user_id']
                }
                
                citation = LegalCitation(**citation_data)
                db.session.add(citation)
                db.session.commit()
                
                # Add to vector database if full_text exists
                if citation.full_text:
                    metadata = {
                        'title': citation.title,
                        'citation': citation.citation,
                        'court': citation.court,
                        'year': citation.year,
                        'legal_area': citation.legal_area,
                        'document_type': citation.document_type
                    }
                    success = vector_search.add_document_to_vector_db(str(citation.id), citation.full_text, metadata)
                    if success:
                        citation.vector_id = str(citation.id)
                        db.session.commit()
                
                success_count += 1
                
            except Exception as e:
                db.session.rollback()
                error_count += 1
                errors.append(f"Row {row_num}: {str(e)}")
        
        # Show results
        if success_count > 0:
            flash(f'Successfully uploaded {success_count} citations!', 'success')
        
        if error_count > 0:
            flash(f'{error_count} errors occurred. Check logs for details.', 'warning')
            for error in errors[:10]:  # Show first 10 errors
                logging.warning(error)
        
        return redirect(url_for('admin_api.admin_panel'))
        
    except Exception as e:
        flash(f'Error processing CSV file: {str(e)}', 'error')
        return redirect(url_for('admin_api.admin_panel'))


# API Endpoints for React frontend

@admin_bp.route('/api/stats', methods=['GET'])
@admin_required
def api_get_stats():
    """Get admin statistics"""
    stats = {
        'total_cases': LegalCitation.query.filter_by(document_type='case').count(),
        'total_acts': LegalCitation.query.filter(
            LegalCitation.document_type.in_(['act', 'statute'])
        ).count(),
        'total_rules': LegalCitation.query.filter_by(document_type='rule').count(),
        'total_users': User.query.count(),
        'total_documents': LegalCitation.query.count()
    }
    
    return jsonify(stats)


@admin_bp.route('/api/recent-uploads', methods=['GET'])
@admin_required
def api_recent_uploads():
    """Get recent uploads"""
    limit = request.args.get('limit', 10, type=int)
    
    recent = LegalCitation.query.order_by(
        LegalCitation.created_at.desc()
    ).limit(limit).all()
    
    return jsonify({
        'uploads': [item.to_dict() for item in recent]
    })


@admin_bp.route('/api/upload-csv', methods=['POST'])
@admin_required
def api_bulk_upload_csv():
    """API endpoint for bulk CSV upload"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Check if citation already exists
                existing = LegalCitation.query.filter_by(citation=row.get('citation')).first()
                if existing:
                    error_count += 1
                    errors.append(f"Row {row_num}: Duplicate citation")
                    continue
                
                # Create and save citation (same logic as above)
                year = int(row.get('year')) if row.get('year') else None
                
                citation_data = {
                    'document_type': row.get('document_type', 'case').lower(),
                    'title': row.get('title', ''),
                    'citation': row.get('citation', ''),
                    'court': row.get('court', ''),
                    'year': year,
                    'legal_area': row.get('legal_area', ''),
                    'summary': row.get('summary', ''),
                    'full_text': row.get('full_text', ''),
                    'uploaded_by': session['user_id']
                }
                
                citation = LegalCitation(**citation_data)
                db.session.add(citation)
                db.session.commit()
                
                success_count += 1
                
            except Exception as e:
                db.session.rollback()
                error_count += 1
                errors.append(f"Row {row_num}: {str(e)}")
        
        return jsonify({
            'success': success_count,
            'errors': error_count,
            'error_details': errors[:10]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/bulk-upload', methods=['GET'])
@admin_required
def bulk_upload_page():
    """Bulk upload page"""
    return render_template('bulk_upload.html')


@admin_bp.route('/api/process-bulk-document', methods=['POST'])
@admin_required
def process_bulk_document():
    """Process a single document from bulk upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not file.filename:
            return jsonify({'success': False, 'message': 'Empty filename'}), 400
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Unsupported file type'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        try:
            # Process document with AI
            result = bulk_processor.process_document(
                file_path, 
                filename, 
                session.get('user_id')
            )
            
            if not result['success']:
                return jsonify(result), 200
            
            # Check for duplicate citation
            existing = LegalCitation.query.filter_by(
                citation=result['data']['citation']
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'Duplicate citation: {result["data"]["citation"]} already exists'
                }), 200
            
            # Save to database
            citation = LegalCitation(**result['data'])
            db.session.add(citation)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'citation': result['citation'],
                'message': f'Successfully added: {result["citation"]}'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing document: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Processing error: {str(e)}'
            }), 200
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
    
    except Exception as e:
        logger.error(f"Error in bulk document processing: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
