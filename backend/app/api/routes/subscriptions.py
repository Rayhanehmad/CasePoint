"""
Subscription API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import stripe

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, SubscriptionTier
from app.models.subscription import Subscription, SubscriptionStatus
from app.api.routes.auth import get_current_user

router = APIRouter()

# Configure Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

# Pydantic models
class SubscriptionPlan(BaseModel):
    tier: str
    name: str
    price_monthly: float
    price_yearly: float
    features: list[str]
    limits: dict

class CreateCheckoutRequest(BaseModel):
    tier: str
    billing_period: str = "monthly"  # monthly or yearly

class SubscriptionInfo(BaseModel):
    id: str
    tier: str
    status: str
    current_period_start: str
    current_period_end: str
    stripe_subscription_id: str

# Subscription plans configuration
SUBSCRIPTION_PLANS = {
    "basic": SubscriptionPlan(
        tier="basic",
        name="Basic Plan",
        price_monthly=29.99,
        price_yearly=299.99,
        features=[
            "Advanced search with filters",
            "Up to 100 searches per month",
            "Basic document upload",
            "Email support"
        ],
        limits={
            "searches_per_month": 100,
            "document_uploads_per_month": 10,
            "storage_mb": 1000
        }
    ),
    "premium": SubscriptionPlan(
        tier="premium",
        name="Premium Plan",
        price_monthly=79.99,
        price_yearly=799.99,
        features=[
            "AI-powered advanced search",
            "Unlimited searches",
            "Bulk document upload",
            "OCR processing",
            "Priority support"
        ],
        limits={
            "searches_per_month": -1,  # unlimited
            "document_uploads_per_month": 100,
            "storage_mb": 10000
        }
    ),
    "enterprise": SubscriptionPlan(
        tier="enterprise",
        name="Enterprise Plan",
        price_monthly=199.99,
        price_yearly=1999.99,
        features=[
            "All Premium features",
            "Custom integrations",
            "API access",
            "Dedicated support",
            "Custom training"
        ],
        limits={
            "searches_per_month": -1,
            "document_uploads_per_month": -1,
            "storage_mb": -1
        }
    )
}

# Routes
@router.get("/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return {
        "plans": list(SUBSCRIPTION_PLANS.values()),
        "current_tier": "free"
    }

@router.get("/current")
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user subscription"""
    
    # Get active subscription
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
        .order_by(Subscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        return {
            "tier": current_user.subscription_tier.value,
            "status": "free",
            "message": "No active subscription"
        }
    
    return SubscriptionInfo(
        id=str(subscription.id),
        tier=subscription.tier,
        status=subscription.status.value,
        current_period_start=subscription.current_period_start.isoformat() if subscription.current_period_start else "",
        current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else "",
        stripe_subscription_id=subscription.stripe_subscription_id or ""
    )

@router.post("/checkout")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create Stripe checkout session"""
    
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing service not configured"
        )
    
    if request.tier not in SUBSCRIPTION_PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription tier"
        )
    
    plan = SUBSCRIPTION_PLANS[request.tier]
    price = plan.price_monthly if request.billing_period == "monthly" else plan.price_yearly
    
    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'KanoonPK {plan.name}',
                        'description': f'{plan.name} - {request.billing_period} billing'
                    },
                    'unit_amount': int(price * 100),  # Stripe uses cents
                    'recurring': {
                        'interval': 'month' if request.billing_period == 'monthly' else 'year'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f'{settings.FRONTEND_URL}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{settings.FRONTEND_URL}/subscription/cancelled',
            client_reference_id=str(current_user.id),
            metadata={
                'user_id': str(current_user.id),
                'tier': request.tier,
                'billing_period': request.billing_period
            }
        )
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel current subscription"""
    
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing service not configured"
        )
    
    # Get active subscription
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription or not subscription.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    try:
        # Cancel in Stripe
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        # Update local record
        subscription.status = SubscriptionStatus.CANCELLED
        await db.commit()
        
        return {
            "message": "Subscription cancelled successfully",
            "cancellation_effective": subscription.current_period_end.isoformat() if subscription.current_period_end else None
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )