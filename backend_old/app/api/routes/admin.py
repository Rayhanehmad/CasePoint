"""
Admin API routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User, SubscriptionTier
from app.models.document import LegalDocument
from app.models.search import SearchLog
from app.models.subscription import Subscription
from app.api.routes.auth import get_current_user

router = APIRouter()

# Pydantic models
class AdminStats(BaseModel):
    total_users: int
    total_documents: int
    total_searches: int
    active_subscriptions: int
    documents_processed_today: int
    searches_today: int

class UserSummary(BaseModel):
    id: str
    email: str
    full_name: str
    subscription_tier: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_search: Optional[datetime]

class DocumentSummary(BaseModel):
    id: str
    title: str
    citation: Optional[str]
    jurisdiction: Optional[str]
    document_type: str
    is_processed: bool
    file_size: int
    created_at: datetime

# Helper functions
def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin access"""
    if current_user.subscription_tier != SubscriptionTier.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Routes
@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard statistics"""
    
    # Total counts
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar()
    
    docs_result = await db.execute(select(func.count(LegalDocument.id)))
    total_documents = docs_result.scalar()
    
    searches_result = await db.execute(select(func.count(SearchLog.id)))
    total_searches = searches_result.scalar()
    
    subs_result = await db.execute(
        select(func.count(Subscription.id)).where(Subscription.status == "active")
    )
    active_subscriptions = subs_result.scalar()
    
    # Today's stats
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    docs_today_result = await db.execute(
        select(func.count(LegalDocument.id)).where(
            LegalDocument.created_at >= today,
            LegalDocument.created_at < tomorrow
        )
    )
    documents_processed_today = docs_today_result.scalar()
    
    searches_today_result = await db.execute(
        select(func.count(SearchLog.id)).where(
            SearchLog.created_at >= today,
            SearchLog.created_at < tomorrow
        )
    )
    searches_today = searches_today_result.scalar()
    
    return AdminStats(
        total_users=total_users or 0,
        total_documents=total_documents or 0,
        total_searches=total_searches or 0,
        active_subscriptions=active_subscriptions or 0,
        documents_processed_today=documents_processed_today or 0,
        searches_today=searches_today or 0
    )

@router.get("/users", response_model=List[UserSummary])
async def get_users(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0)
):
    """Get users list"""
    
    # Get users with their last search time
    query = select(User).offset(offset).limit(limit).order_by(desc(User.created_at))
    result = await db.execute(query)
    users = result.scalars().all()
    
    users_data = []
    for user in users:
        # Get last search time
        last_search_result = await db.execute(
            select(SearchLog.created_at)
            .where(SearchLog.user_id == user.id)
            .order_by(desc(SearchLog.created_at))
            .limit(1)
        )
        last_search = last_search_result.scalar_one_or_none()
        
        users_data.append(UserSummary(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            subscription_tier=user.subscription_tier.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_search=last_search
        ))
    
    return users_data

@router.get("/documents", response_model=List[DocumentSummary])
async def get_documents(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    processed_only: bool = Query(False)
):
    """Get documents list"""
    
    query = select(LegalDocument)
    
    if processed_only:
        query = query.where(LegalDocument.is_processed == True)
    
    query = query.offset(offset).limit(limit).order_by(desc(LegalDocument.created_at))
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [
        DocumentSummary(
            id=str(doc.id),
            title=doc.title,
            citation=doc.citation,
            jurisdiction=doc.jurisdiction,
            document_type=doc.document_type,
            is_processed=doc.is_processed,
            file_size=doc.file_size or 0,
            created_at=doc.created_at
        )
        for doc in documents
    ]

@router.patch("/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: str,
    subscription_tier: SubscriptionTier,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user subscription tier"""
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.subscription_tier = subscription_tier
    await db.commit()
    
    return {
        "message": f"User subscription updated to {subscription_tier.value}",
        "user_id": user_id,
        "new_tier": subscription_tier.value
    }

@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user active status"""
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = is_active
    await db.commit()
    
    return {
        "message": f"User {'activated' if is_active else 'deactivated'}",
        "user_id": user_id,
        "is_active": is_active
    }