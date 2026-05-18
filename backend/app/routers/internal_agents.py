import uuid
import bcrypt
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import settings
from app.models.subscription import BlogPost, Subscription, ResearchTrend, AgentRun, SubscriptionTier, CreditUsage
from app.models.user import User
from app.models.resume import Resume
from app.models.optimization import Optimization
from app.models.job_description import JobDescription

router = APIRouter(prefix="/api/v1/internal/agents", tags=["internal"])


async def verify_internal(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or auth.split(" ")[1] != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal key")


# --- Content Ingestion (receives posts from Paperclip Publisher) ---

@router.post("/content", status_code=status.HTTP_201_CREATED)
async def ingest_content(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await verify_internal(request)
    body = await request.json()

    slug = body.get("slug")
    if not slug:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="slug required")

    existing = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")

    post = BlogPost(
        slug=slug,
        title=body.get("title", slug),
        content_md=body.get("content_md", body.get("content", "")),
        meta_description=body.get("meta_description"),
        keywords=body.get("keywords"),
        category=body.get("category", body.get("category")),
        is_published=True,
        published_at=datetime.utcnow() if body.get("published", True) else None,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return {
        "id": str(post.id),
        "slug": post.slug,
        "url": f"{settings.NEXT_PUBLIC_APP_URL}/blog/{post.slug}",
    }


# --- Financial (daily Stripe sync + MRR) ---

@router.post("/financial")
async def run_financial_agent(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await verify_internal(request)

    agent_run = AgentRun(agent_name="financial", status="running")
    db.add(agent_run)
    await db.commit()

    try:
        result = await db.execute(
            select(Subscription).where(Subscription.status == "active")
        )
        active_subs = result.scalars().all()

        result = await db.execute(
            select(Subscription, SubscriptionTier)
            .join(SubscriptionTier, Subscription.tier_id == SubscriptionTier.id)
            .where(Subscription.status == "active")
        )
        sub_rows = result.all()

        mrr_cents = sum(t.monthly_price_cents or 0 for _, t in sub_rows)
        paying_users = len([s for s, _ in sub_rows if (s.stripe_customer_id and (s.stripe_subscription_id))])

        month_ago = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(func.count()).select_from(Subscription).where(Subscription.created_at >= month_ago)
        )
        new_subs = result.scalar() or 0

        result = await db.execute(
            select(func.count()).select_from(Subscription).where(Subscription.status == "canceled", Subscription.created_at >= month_ago)
        )
        churned = result.scalar() or 0

        churn_rate = round((churned / (paying_users + churned) * 100) if (paying_users + churned) > 0 else 0, 1)

        data = {
            "date": date.today().isoformat(),
            "mrr_cents": mrr_cents,
            "mrr_dollars": round(mrr_cents / 100, 2),
            "active_subscriptions": len(active_subs),
            "paying_users": paying_users,
            "new_subs_30d": new_subs,
            "churned_30d": churned,
            "churn_rate_pct": churn_rate,
        }

        agent_run.status = "completed"
        agent_run.output_path = f"data/financials/daily_mrr_{date.today().isoformat()}.json"
        agent_run.completed_at = datetime.utcnow()
        await db.commit()

        return data

    except Exception as e:
        agent_run.status = "failed"
        agent_run.error_message = str(e)
        agent_run.completed_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# --- Research Data Ingestion (receives Reddit data from laptop browser agent) ---

@router.post("/research", status_code=status.HTTP_201_CREATED)
async def ingest_research(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await verify_internal(request)
    body = await request.json()

    trend = ResearchTrend(
        project_key=body.get("project_key", "resume_optimizer"),
        subreddit_browses=body.get("subreddit_browses"),
        keyword_searches=body.get("keyword_searches"),
    )
    db.add(trend)
    await db.commit()
    await db.refresh(trend)

    return {"id": str(trend.id), "created_at": trend.created_at.isoformat()}


# --- Research Data Retrieval (for admin dashboard) ---

@router.get("/research")
async def get_research(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await verify_internal(request)
    result = await db.execute(
        select(ResearchTrend).order_by(ResearchTrend.created_at.desc()).limit(20)
    )
    trends = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "project_key": t.project_key,
            "subreddit_browses": t.subreddit_browses,
            "keyword_searches": t.keyword_searches,
            "created_at": t.created_at.isoformat(),
        }
        for t in trends
    ]


# --- User Management ---

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await verify_internal(request)
    body = await request.json()
    email = body.get("email")
    password = body.get("password", "changeme123")
    full_name = body.get("full_name")
    tier_name = body.get("tier", "free")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email required")

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=email,
        full_name=full_name,
        password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        auth_provider="email",
        email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    if tier_name != "free":
        tier_result = await db.execute(select(SubscriptionTier).where(SubscriptionTier.name == tier_name))
        tier = tier_result.scalar_one_or_none()
        if tier:
            sub = Subscription(user_id=user.id, tier_id=tier.id, status="active")
            db.add(sub)
            await db.commit()

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "tier": tier_name,
    }


@router.get("/users")
async def list_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await verify_internal(request)
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    output = []
    for u in users:
        sub_result = await db.execute(
            select(Subscription, SubscriptionTier)
            .join(SubscriptionTier, Subscription.tier_id == SubscriptionTier.id)
            .where(Subscription.user_id == u.id, Subscription.status == "active")
            .order_by(Subscription.created_at.desc())
        )
        sub_row = sub_result.first()

        opt_result = await db.execute(
            select(func.count()).select_from(Optimization).where(Optimization.user_id == u.id)
        )
        opt_count = opt_result.scalar() or 0

        tier_name = None
        if sub_row:
            _, tier = sub_row
            tier_name = tier.name

        output.append({
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "auth_provider": u.auth_provider,
            "email_verified": u.email_verified,
            "tier": tier_name or "free",
            "optimizations": opt_count,
            "created_at": u.created_at.isoformat(),
        })

    return output


@router.put("/users/{user_id}/tier")
async def assign_user_tier(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await verify_internal(request)
    body = await request.json()
    tier_name = body.get("tier")

    tier_result = await db.execute(select(SubscriptionTier).where(SubscriptionTier.name == tier_name))
    tier = tier_result.scalar_one_or_none()
    if not tier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tier not found")

    existing = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id, Subscription.status == "active")
    )
    sub = existing.scalar_one_or_none()

    if sub:
        sub.tier_id = tier.id
    else:
        sub = Subscription(user_id=user_id, tier_id=tier.id, status="active")
        db.add(sub)

    await db.commit()
    return {"status": "ok", "user_id": str(user_id), "tier": tier_name}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await verify_internal(request)
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    credit_rows = (await db.execute(select(CreditUsage).where(CreditUsage.user_id == user_id))).scalars().all()
    for cr in credit_rows:
        await db.delete(cr)

    sub_rows = (await db.execute(select(Subscription).where(Subscription.user_id == user_id))).scalars().all()
    for s in sub_rows:
        await db.delete(s)

    opt_rows = (await db.execute(select(Optimization).where(Optimization.user_id == user_id))).scalars().all()
    for o in opt_rows:
        await db.delete(o)

    jd_rows = (await db.execute(select(JobDescription).where(JobDescription.user_id == user_id))).scalars().all()
    for jd in jd_rows:
        await db.delete(jd)

    resume_rows = (await db.execute(select(Resume).where(Resume.user_id == user_id))).scalars().all()
    for r in resume_rows:
        await db.delete(r)

    await db.delete(user)
    await db.commit()


# --- Tier Management ---

@router.get("/tiers")
async def list_tiers(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await verify_internal(request)
    result = await db.execute(select(SubscriptionTier).order_by(SubscriptionTier.name))
    tiers = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "stripe_price_id": t.stripe_price_id,
            "monthly_price_cents": t.monthly_price_cents,
            "credits_per_month": t.credits_per_month,
            "features": t.features,
            "is_active": t.is_active,
        }
        for t in tiers
    ]


@router.put("/tiers/{tier_id}")
async def update_tier(
    tier_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await verify_internal(request)
    body = await request.json()

    result = await db.execute(select(SubscriptionTier).where(SubscriptionTier.id == tier_id))
    tier = result.scalar_one_or_none()
    if not tier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tier not found")

    for field in ("name", "stripe_price_id", "monthly_price_cents", "credits_per_month", "features", "is_active"):
        if field in body:
            setattr(tier, field, body[field])

    await db.commit()
    await db.refresh(tier)
    return {
        "id": str(tier.id),
        "name": tier.name,
        "monthly_price_cents": tier.monthly_price_cents,
        "credits_per_month": tier.credits_per_month,
        "features": tier.features,
        "is_active": tier.is_active,
    }


# --- Model Configuration Display ---

@router.get("/models")
async def get_models(
    request: Request,
):
    await verify_internal(request)
    from app.config import settings as s
    return {
        "rewrite": s.AI_MODEL_REWRITE,
        "parse": s.AI_MODEL_PARSE,
        "extract": s.AI_MODEL_EXTRACT,
        "cover_letter": s.AI_MODEL_COVER_LETTER,
        "embedding": s.EMBEDDING_MODEL,
        "cloud_base_url": s.OLLAMA_CLOUD_BASE_URL,
        "local_url": s.LOCAL_OLLAMA_URL,
    }
