import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import verify_token
from app.models.subscription import BlogPost
from app.services.jd_extractor import extract_jd_keywords
from app.services.scoring import keyword_coverage_score
from app.services.embedding import cosine_similarity, generate_embedding

router = APIRouter(prefix="/api/v1/content", tags=["content"])


# --- Admin Blog CRUD ---

@router.post("/blog", status_code=status.HTTP_201_CREATED)
async def create_blog_post(
    body: dict,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    post = BlogPost(
        slug=body["slug"],
        title=body["title"],
        content_md=body.get("content_md"),
        meta_description=body.get("meta_description"),
        keywords=body.get("keywords"),
        category=body.get("category"),
        is_published=body.get("is_published", False),
        published_at=datetime.utcnow() if body.get("is_published") else None,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return _post_response(post)


@router.get("/blog")
async def list_blog_posts(
    published_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    query = select(BlogPost).order_by(BlogPost.published_at.desc())
    if published_only:
        query = query.where(BlogPost.is_published == True)
    result = await db.execute(query)
    posts = result.scalars().all()
    return [_post_response(p) for p in posts]


@router.get("/blog/{slug}")
async def get_blog_post(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return _post_response(post)


@router.put("/blog/{slug}")
async def update_blog_post(
    slug: str,
    body: dict,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for field in ("title", "content_md", "meta_description", "keywords", "category", "is_published"):
        if field in body:
            setattr(post, field, body[field])

    if body.get("is_published") and not post.published_at:
        post.published_at = datetime.utcnow()

    await db.commit()
    await db.refresh(post)
    return _post_response(post)


@router.delete("/blog/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog_post(
    slug: str,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    post = result.scalar_one_or_none()
    if post:
        await db.delete(post)
        await db.commit()


# --- Free Tools ---

@router.post("/tools/keyword-extractor")
async def extract_keywords(body: dict, db: AsyncSession = Depends(get_db)):
    text = body.get("text", "")
    if not text or len(text) < 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text too short (min 50 characters)")

    try:
        keywords = await extract_jd_keywords(text)
        return {"keywords": keywords}
    except Exception:
        return {"keywords": {"error": "Extraction unavailable"}, "source": "text"}


@router.post("/tools/resume-score")
async def score_resume(body: dict, db: AsyncSession = Depends(get_db)):
    resume_text = body.get("resume_text", "")
    jd_text = body.get("jd_text", "")

    if not resume_text or not jd_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both resume_text and jd_text required")

    try:
        resume_emb = await generate_embedding(resume_text[:8000])
        jd_emb = await generate_embedding(jd_text[:8000])
        emb_score = round(float(cosine_similarity(resume_emb, jd_emb) * 100), 1)
    except Exception:
        emb_score = None

    kw_score = None
    try:
        jd_kw = await extract_jd_keywords(jd_text)
        kw_score = keyword_coverage_score(resume_text, jd_kw)
    except Exception:
        pass

    return {
        "overall_score": emb_score or kw_score or 0,
        "embedding_score": emb_score,
        "keyword_coverage": kw_score,
    }


def _post_response(post: BlogPost) -> dict:
    return {
        "id": str(post.id),
        "slug": post.slug,
        "title": post.title,
        "content_md": post.content_md,
        "meta_description": post.meta_description,
        "keywords": post.keywords,
        "category": post.category,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "is_published": post.is_published,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }
