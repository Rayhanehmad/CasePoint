"""
Search API routes
"""

import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, text
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User, SubscriptionTier
from app.models.document import LegalDocument
from app.models.search import SearchLog
from app.api.routes.auth import get_current_user
from app.core.exceptions import SubscriptionException
from app.services.ai_service import AIService

router = APIRouter()

# Pydantic models
class SearchFilters(BaseModel):
    jurisdiction: Optional[str] = None
    court_level: Optional[str] = None
    legal_area: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    document_type: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    search_type: str = "basic"  # basic, advanced, ai_advanced
    filters: Optional[SearchFilters] = None
    limit: int = 20
    offset: int = 0

class DocumentResult(BaseModel):
    id: str
    title: str
    citation: Optional[str]
    jurisdiction: Optional[str]
    court_level: Optional[str]
    legal_area: Optional[str]
    date_decided: Optional[str]
    extracted_text_preview: str
    relevance_score: Optional[float] = None
    file_path: str
    document_type: str

class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: List[DocumentResult]
    total_results: int
    execution_time_ms: int
    ai_response: Optional[str] = None

# Helper functions
def check_search_permissions(user: User, search_type: str):
    """Check if user has permission for search type"""
    if search_type == "basic":
        return True  # Basic search allowed for all
    
    if search_type in ["advanced", "ai_advanced"]:
        if user.subscription_tier == SubscriptionTier.FREE:
            raise SubscriptionException("Advanced search requires paid subscription")
        return True
    
    return False

async def log_search(
    db: AsyncSession,
    user_id: str,
    query: str,
    search_type: str,
    filters: Dict[str, Any],
    results_count: int,
    execution_time_ms: int
):
    """Log search activity"""
    search_log = SearchLog(
        user_id=user_id,
        query=query,
        search_type=search_type,
        filters=filters,
        results_count=results_count,
        execution_time_ms=execution_time_ms
    )
    db.add(search_log)
    await db.commit()

# Routes
@router.post("/", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search legal documents"""
    start_time = time.time()
    
    # Check permissions
    check_search_permissions(current_user, search_request.search_type)
    
    # Build query
    query = select(LegalDocument).where(LegalDocument.is_processed == True)
    
    # Add text search
    if search_request.query:
        query = query.where(
            or_(
                LegalDocument.title.ilike(f"%{search_request.query}%"),
                LegalDocument.extracted_text.ilike(f"%{search_request.query}%"),
                LegalDocument.citation.ilike(f"%{search_request.query}%")
            )
        )
    
    # Apply filters
    if search_request.filters:
        if search_request.filters.jurisdiction:
            query = query.where(LegalDocument.jurisdiction.ilike(f"%{search_request.filters.jurisdiction}%"))
        if search_request.filters.court_level:
            query = query.where(LegalDocument.court_level.ilike(f"%{search_request.filters.court_level}%"))
        if search_request.filters.legal_area:
            query = query.where(LegalDocument.legal_area.ilike(f"%{search_request.filters.legal_area}%"))
        if search_request.filters.document_type:
            query = query.where(LegalDocument.document_type == search_request.filters.document_type)
        if search_request.filters.date_from:
            query = query.where(LegalDocument.date_decided >= search_request.filters.date_from)
        if search_request.filters.date_to:
            query = query.where(LegalDocument.date_decided <= search_request.filters.date_to)
    
    # Execute query with pagination
    query = query.offset(search_request.offset).limit(search_request.limit)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Count total results
    count_query = select(LegalDocument).where(LegalDocument.is_processed == True)
    if search_request.query:
        count_query = count_query.where(
            or_(
                LegalDocument.title.ilike(f"%{search_request.query}%"),
                LegalDocument.extracted_text.ilike(f"%{search_request.query}%"),
                LegalDocument.citation.ilike(f"%{search_request.query}%")
            )
        )
    total_result = await db.execute(select(text("COUNT(*)")).select_from(count_query.subquery()))
    total_count = total_result.scalar()
    
    # Process results
    results = []
    for doc in documents:
        preview_text = (doc.extracted_text or "")[:500] + "..." if doc.extracted_text and len(doc.extracted_text) > 500 else doc.extracted_text or ""
        
        results.append(DocumentResult(
            id=str(doc.id),
            title=doc.title,
            citation=doc.citation,
            jurisdiction=doc.jurisdiction,
            court_level=doc.court_level,
            legal_area=doc.legal_area,
            date_decided=doc.date_decided.isoformat() if doc.date_decided else None,
            extracted_text_preview=preview_text,
            file_path=doc.file_path,
            document_type=doc.document_type
        ))
    
    execution_time = int((time.time() - start_time) * 1000)
    
    # AI Advanced Search
    ai_response = None
    if search_request.search_type == "ai_advanced":
        try:
            ai_service = AIService()
            ai_response = await ai_service.generate_legal_analysis(
                search_request.query,
                [doc.extracted_text for doc in documents if doc.extracted_text]
            )
        except Exception as e:
            print(f"AI service error: {e}")
    
    # Log search
    filters_dict = search_request.filters.dict() if search_request.filters else {}
    await log_search(
        db, str(current_user.id), search_request.query, search_request.search_type,
        filters_dict, len(results), execution_time
    )
    
    return SearchResponse(
        query=search_request.query,
        search_type=search_request.search_type,
        results=results,
        total_results=total_count,
        execution_time_ms=execution_time,
        ai_response=ai_response
    )

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get search suggestions"""
    
    # Get suggestions from document titles and citations
    query = select(LegalDocument.title, LegalDocument.citation).where(
        and_(
            LegalDocument.is_processed == True,
            or_(
                LegalDocument.title.ilike(f"%{q}%"),
                LegalDocument.citation.ilike(f"%{q}%")
            )
        )
    ).limit(10)
    
    result = await db.execute(query)
    suggestions = []
    
    for title, citation in result:
        if title and q.lower() in title.lower():
            suggestions.append({"text": title, "type": "title"})
        if citation and q.lower() in citation.lower():
            suggestions.append({"text": citation, "type": "citation"})
    
    return {"suggestions": suggestions[:10]}