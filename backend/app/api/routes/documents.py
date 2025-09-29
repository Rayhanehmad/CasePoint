"""
Document API routes
"""

import os
import hashlib
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.document import LegalDocument
from app.api.routes.auth import get_current_user
from app.services.ocr_service import OCRService

router = APIRouter()

# Pydantic models
class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    size: int
    status: str
    message: str

class DocumentInfo(BaseModel):
    id: str
    title: str
    citation: str
    jurisdiction: str
    court_level: str
    legal_area: str
    document_type: str
    original_filename: str
    file_size: int
    is_processed: bool
    ocr_confidence: float
    created_at: str

# Helper functions
def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA-256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in settings.ALLOWED_EXTENSIONS

# Routes
@router.post("/upload", response_model=List[DocumentUploadResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload legal documents"""
    
    responses = []
    
    for file in files:
        try:
            # Validate file
            if not is_allowed_file(file.filename):
                responses.append(DocumentUploadResponse(
                    id="",
                    filename=file.filename,
                    size=0,
                    status="error",
                    message=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
                ))
                continue
            
            # Read file content
            content = await file.read()
            
            # Check file size
            if len(content) > settings.MAX_FILE_SIZE:
                responses.append(DocumentUploadResponse(
                    id="",
                    filename=file.filename,
                    size=len(content),
                    status="error",
                    message=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
                ))
                continue
            
            # Calculate hash and check for duplicates
            file_hash = calculate_file_hash(content)
            result = await db.execute(select(LegalDocument).where(LegalDocument.file_hash == file_hash))
            if result.scalar_one_or_none():
                responses.append(DocumentUploadResponse(
                    id="",
                    filename=file.filename,
                    size=len(content),
                    status="error",
                    message="File already exists in the database"
                ))
                continue
            
            # Save file
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            save_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(settings.DOCUMENTS_DIR, save_filename)
            
            # Ensure directory exists
            os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
            
            # Write file
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Create database record
            document = LegalDocument(
                id=file_id,
                title=os.path.splitext(file.filename)[0],
                original_filename=file.filename,
                file_path=file_path,
                file_size=len(content),
                file_hash=file_hash,
                document_type=file_extension[1:] if file_extension else "unknown",
                uploaded_by=current_user.id,
                is_processed=False
            )
            
            db.add(document)
            await db.commit()
            
            # Queue for OCR processing (in background)
            # TODO: Implement background task processing
            
            responses.append(DocumentUploadResponse(
                id=file_id,
                filename=file.filename,
                size=len(content),
                status="success",
                message="File uploaded successfully. Processing will begin shortly."
            ))
            
        except Exception as e:
            responses.append(DocumentUploadResponse(
                id="",
                filename=file.filename,
                size=0,
                status="error",
                message=f"Upload failed: {str(e)}"
            ))
    
    return responses

@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document information"""
    
    result = await db.execute(select(LegalDocument).where(LegalDocument.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentInfo(
        id=str(document.id),
        title=document.title,
        citation=document.citation or "",
        jurisdiction=document.jurisdiction or "",
        court_level=document.court_level or "",
        legal_area=document.legal_area or "",
        document_type=document.document_type,
        original_filename=document.original_filename,
        file_size=document.file_size,
        is_processed=document.is_processed,
        ocr_confidence=float(document.ocr_confidence) if document.ocr_confidence else 0.0,
        created_at=document.created_at.isoformat()
    )

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download original document file"""
    
    result = await db.execute(select(LegalDocument).where(LegalDocument.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=document.file_path,
        filename=document.original_filename,
        media_type="application/octet-stream"
    )

@router.get("/{document_id}/text")
async def get_document_text(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get extracted text from document"""
    
    result = await db.execute(select(LegalDocument).where(LegalDocument.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "document_id": str(document.id),
        "extracted_text": document.extracted_text or "",
        "ocr_confidence": float(document.ocr_confidence) if document.ocr_confidence else None,
        "is_processed": document.is_processed
    }

@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger document reprocessing"""
    
    result = await db.execute(select(LegalDocument).where(LegalDocument.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Reset processing status
    document.is_processed = False
    document.extracted_text = None
    document.ocr_confidence = None
    
    await db.commit()
    
    # TODO: Queue for reprocessing
    
    return {
        "message": "Document queued for reprocessing",
        "document_id": str(document.id)
    }