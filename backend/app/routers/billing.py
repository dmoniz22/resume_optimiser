import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import stripe as stripe_lib
from app.database import get_db
from app.auth import verify_token
from app.models.user import User
from app.models.subscription import SubscriptionTier, Subscription
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["billing"])


@router.get("/stripe/portal")
async def stripe_portal(
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == token["user_id"],
            Subscription.status == "active",
        )
    )
    sub = result.scalar_one_or_none()

    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")

    stripe_lib.api_key = settings.STRIPE_SECRET_KEY
    session = stripe_lib.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.NEXT_PUBLIC_APP_URL}/dashboard",
    )
    return RedirectResponse(url=session.url)


@router.post("/stripe/checkout")
async def create_checkout_session(
    request: Request,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    body = await request.json()
    price_id = body.get("price_id")
    if not price_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="price_id required")

    stripe_lib.api_key = settings.STRIPE_SECRET_KEY

    result = await db.execute(select(User).where(User.id == token["user_id"]))
    user = result.scalar_one_or_none()

    session = stripe_lib.checkout.Session.create(
        customer_email=user.email if user else None,
        client_reference_id=token["user_id"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.NEXT_PUBLIC_APP_URL}/dashboard?checkout=success",
        cancel_url=f"{settings.NEXT_PUBLIC_APP_URL}/pricing",
        metadata={"user_id": token["user_id"]},
    )
    return {"url": session.url}


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    stripe_lib.api_key = settings.STRIPE_SECRET_KEY
    try:
        event = stripe_lib.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe_lib.error.SignatureVerificationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        await handle_checkout_completed(event["data"]["object"], db)
    elif event["type"] == "customer.subscription.updated":
        await handle_subscription_updated(event["data"]["object"], db)
    elif event["type"] == "customer.subscription.deleted":
        await handle_subscription_deleted(event["data"]["object"], db)

    return {"status": "ok"}


async def handle_checkout_completed(session_obj: dict, db: AsyncSession):
    user_id = session_obj.get("client_reference_id") or session_obj.get("metadata", {}).get("user_id")
    if not user_id:
        return

    customer_id = session_obj.get("customer")
    subscription_id = session_obj.get("subscription")

    result = await db.execute(select(SubscriptionTier))
    tiers = {t.stripe_price_id: t for t in result.scalars().all() if t.stripe_price_id}

    price_id = None
    if subscription_id:
        stripe_lib.api_key = settings.STRIPE_SECRET_KEY
        sub = stripe_lib.Subscription.retrieve(subscription_id)
        if sub and sub.get("items", {}).get("data"):
            price_id = sub["items"]["data"][0].get("price", {}).get("id")

    tier = tiers.get(price_id) if price_id else None
    if not tier:
        return

    sub_row = Subscription(
        user_id=uuid.UUID(user_id),
        tier_id=tier.id,
        stripe_subscription_id=subscription_id,
        stripe_customer_id=customer_id,
        status="active",
    )
    db.add(sub_row)
    await db.commit()


async def handle_subscription_updated(subscription_obj: dict, db: AsyncSession):
    sub_id = subscription_obj.get("id")
    status_val = subscription_obj.get("status")

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.status = status_val
        sub.current_period_start = datetime.utcfromtimestamp(subscription_obj.get("current_period_start", 0))
        sub.current_period_end = datetime.utcfromtimestamp(subscription_obj.get("current_period_end", 0))
        sub.cancel_at_period_end = subscription_obj.get("cancel_at_period_end", False)
        await db.commit()


async def handle_subscription_deleted(subscription_obj: dict, db: AsyncSession):
    sub_id = subscription_obj.get("id")
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.status = "canceled"
        await db.commit()
