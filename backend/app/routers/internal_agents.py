import uuid
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import settings
from app.models.subscription import BlogPost, Subscription, ResearchTrend, AgentRun, SubscriptionTier

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
