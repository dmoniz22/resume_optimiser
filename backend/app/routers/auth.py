import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import create_access_token, verify_token
from app.models.user import User
from app.models.subscription import SubscriptionTier, Subscription, CreditUsage
from app.schemas.user import UserCreate, UserResponse, AccountResponse
from app.config import settings
import bcrypt

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=data.email,
        full_name=data.full_name,
        password_hash=bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode(),
        auth_provider="email",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/account", response_model=AccountResponse)
async def account(
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    user = await db.execute(select(User).where(User.id == token["user_id"]))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    subscription_result = await db.execute(
        select(Subscription, SubscriptionTier)
        .join(SubscriptionTier, Subscription.tier_id == SubscriptionTier.id)
        .where(Subscription.user_id == user.id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
    )
    sub_row = subscription_result.first()

    tier_name = "free"
    tier_features = None
    sub_status = None
    credits_limit = None

    if sub_row:
        sub, tier = sub_row
        tier_name = tier.name
        tier_features = tier.features
        sub_status = sub.status
        if tier.credits_per_month is not None:
            credits_limit = tier.credits_per_month
    else:
        free_tier = await db.execute(select(SubscriptionTier).where(SubscriptionTier.name == "free"))
        free_tier = free_tier.scalar_one_or_none()
        if free_tier:
            tier_features = free_tier.features
            credits_limit = free_tier.credits_per_month

    today = date.today()
    month_start = today.replace(day=1)
    credit_result = await db.execute(
        select(CreditUsage).where(
            CreditUsage.user_id == user.id,
            CreditUsage.month_start == month_start,
        )
    )
    credit_usage = credit_result.scalar_one_or_none()
    credits_used = credit_usage.credits_used if credit_usage else 0

    return AccountResponse(
        user=UserResponse.model_validate(user),
        tier=tier_name,
        tier_features=tier_features,
        credits_used_this_month=credits_used,
        credits_limit=credits_limit,
        subscription_status=sub_status,
    )


@router.post("/verify")
async def verify_credentials(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(select(User).where(User.email == body.email))
    user = user_result.scalar_one_or_none()
    if not user or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not bcrypt.checkpw(body.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(str(user.id), user.email)
    return {
        "token": token,
        "user": UserResponse.model_validate(user).model_dump(),
    }
