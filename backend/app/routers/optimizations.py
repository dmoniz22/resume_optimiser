import uuid
import asyncio
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, AsyncSessionLocal
from app.auth import verify_token
from app.models.optimization import Optimization
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.subscription import CreditUsage, SubscriptionTier, Subscription
from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationInitResponse,
    OptimizationListResponse,
)
from app.services.scoring import calculate_pre_score, calculate_post_score
from app.services.optimizer import identify_gaps, extract_bullets_from_resume, rewrite_bullets
from app.services.pdf_generator import generate_pdf, generate_cover_letter_pdf
from app.services.cover_letter import generate_cover_letter_text
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["optimizations"])


async def check_credits(user_id: uuid.UUID, db: AsyncSession) -> bool:
    result = await db.execute(
        select(Subscription, SubscriptionTier)
        .join(SubscriptionTier, Subscription.tier_id == SubscriptionTier.id)
        .where(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
    )
    sub_row = result.first()

    if sub_row:
        _, tier = sub_row
        if tier.credits_per_month is None:
            return True

    month_start = date.today().replace(day=1)
    result = await db.execute(
        select(CreditUsage).where(
            CreditUsage.user_id == user_id,
            CreditUsage.month_start == month_start,
        )
    )
    usage = result.scalar_one_or_none()

    limit = 3
    if sub_row:
        _, tier = sub_row
        if tier.credits_per_month:
            limit = tier.credits_per_month

    if not usage:
        db.add(CreditUsage(user_id=user_id, month_start=month_start, credits_used=0))
        await db.commit()
        return True

    return usage.credits_used < limit


async def record_credit_use(user_id: uuid.UUID, db: AsyncSession):
    month_start = date.today().replace(day=1)
    result = await db.execute(
        select(CreditUsage).where(
            CreditUsage.user_id == user_id,
            CreditUsage.month_start == month_start,
        )
    )
    usage = result.scalar_one_or_none()
    if usage:
        usage.credits_used += 1
    else:
        db.add(CreditUsage(user_id=user_id, month_start=month_start, credits_used=1))
    await db.commit()


@router.post("/optimize", response_model=OptimizationInitResponse, status_code=status.HTTP_201_CREATED)
async def start_optimization(
    data: OptimizationRequest,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    has_credits = await check_credits(token["user_id"], db)
    if not has_credits:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="No credits remaining this month")

    resume_result = await db.execute(
        select(Resume).where(Resume.id == data.resume_id, Resume.user_id == token["user_id"])
    )
    resume = resume_result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    jd_result = await db.execute(
        select(JobDescription).where(JobDescription.id == data.jd_id, JobDescription.user_id == token["user_id"])
    )
    jd = jd_result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    optimization = Optimization(
        user_id=token["user_id"],
        resume_id=data.resume_id,
        jd_id=data.jd_id,
        status="processing",
    )
    db.add(optimization)
    await db.commit()
    await db.refresh(optimization)

    return OptimizationInitResponse(id=optimization.id, status="processing")


@router.get("/optimizations", response_model=OptimizationListResponse)
async def list_optimizations(
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Optimization)
        .where(Optimization.user_id == token["user_id"])
        .order_by(Optimization.created_at.desc())
    )
    optimizations = result.scalars().all()
    return OptimizationListResponse(
        optimizations=[OptimizationResponse.model_validate(o) for o in optimizations],
        total=len(optimizations),
    )


@router.get("/optimizations/{optimization_id}", response_model=OptimizationResponse)
async def get_optimization(
    optimization_id: uuid.UUID,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Optimization).where(
            Optimization.id == optimization_id,
            Optimization.user_id == token["user_id"],
        )
    )
    optimization = result.scalar_one_or_none()
    if not optimization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization not found")
    return optimization


@router.post("/optimizations/{optimization_id}/process", response_model=OptimizationResponse)
async def process_optimization(
    optimization_id: uuid.UUID,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Optimization).where(
            Optimization.id == optimization_id,
            Optimization.user_id == token["user_id"],
        )
    )
    optimization = result.scalar_one_or_none()
    if not optimization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization not found")

    if optimization.status not in ("pending", "processing"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Optimization already completed or failed")

    optimization.status = "processing"
    await db.commit()

    asyncio.create_task(_run_optimization_pipeline(str(optimization_id), token["user_id"]))

    return optimization


async def _run_optimization_pipeline(optimization_id: str, user_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Optimization).where(Optimization.id == optimization_id))
        optimization = result.scalar_one_or_none()
        if not optimization:
            return

        start_time = datetime.utcnow()

        try:
            resume_result = await db.execute(select(Resume).where(Resume.id == optimization.resume_id))
            resume = resume_result.scalar_one_or_none()
            jd_result = await db.execute(select(JobDescription).where(JobDescription.id == optimization.jd_id))
            jd = jd_result.scalar_one_or_none()

            if not resume or not jd:
                raise ValueError("Resume or JD not found")

            if not resume.parsed_text:
                optimization.status = "failed"
                optimization.error_message = "Resume text not extracted"
                await db.commit()
                return

            pre_score = await calculate_pre_score(str(resume.id), str(jd.id), db)

            resume_structured = resume.structured_data or {}
            jd_keywords = jd.extracted_keywords or {}

            gaps = identify_gaps(resume_structured, jd_keywords)
            bullets = extract_bullets_from_resume(resume_structured)
            if not bullets and resume_structured:
                bullets = [{"section": "Content", "bullet_index": i, "text": resume.parsed_text.split("\n")[i]}
                           for i in range(min(20, len(resume.parsed_text.split("\n")))) if resume.parsed_text.split("\n")[i].strip()]

            original_bullets_data = [{"section": b["section"], "bullet_index": b["bullet_index"], "text": b["text"]} for b in bullets]
            keywords_str = ", ".join(gaps[:30]) if gaps else ", ".join(jd_keywords.get("hard_skills", []) + jd_keywords.get("soft_skills", []))

            optimized_bullets, fabrication_flags = await rewrite_bullets(
                bullets, keywords_str, resume.parsed_text or ""
            )

            resume.structured_data = resume_structured
            await db.commit()

            post_score = await calculate_post_score(str(resume.id), str(jd.id), db)

            optimization.pre_score = pre_score
            optimization.post_score = post_score
            optimization.original_bullets = original_bullets_data
            optimization.optimized_bullets = optimized_bullets
            optimization.fabrication_flags = fabrication_flags
            optimization.model_used = settings.AI_MODEL_REWRITE

            pdf_path = await generate_pdf(str(optimization.id), resume_structured, optimized_bullets)
            optimization.output_file_path = pdf_path

            try:
                cover_body = await generate_cover_letter_text(
                    resume.parsed_text or "",
                    jd.raw_text,
                )
                optimization.cover_letter_text = cover_body
            except Exception:
                pass

            optimization.status = "completed"
            optimization.processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await record_credit_use(user_id, db)
            await db.commit()

        except Exception as e:
            optimization.status = "failed"
            optimization.error_message = str(e)
            await db.commit()


@router.post("/optimizations/{optimization_id}/regenerate", response_model=OptimizationResponse)
async def regenerate_bullet(
    optimization_id: uuid.UUID,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Optimization).where(
            Optimization.id == optimization_id,
            Optimization.user_id == token["user_id"],
        )
    )
    optimization = result.scalar_one_or_none()
    if not optimization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization not found")

    resume_result = await db.execute(select(Resume).where(Resume.id == optimization.resume_id))
    resume = resume_result.scalar_one_or_none()
    jd_result = await db.execute(select(JobDescription).where(JobDescription.id == optimization.jd_id))
    jd = jd_result.scalar_one_or_none()

    if not resume or not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    bullets = extract_bullets_from_resume(resume.structured_data or {})
    jd_keywords = jd.extracted_keywords or {}
    keywords_str = ", ".join(jd_keywords.get("hard_skills", []) + jd_keywords.get("soft_skills", []))

    optimized_bullets, fabrication_flags = await rewrite_bullets(
        bullets, keywords_str, resume.parsed_text or ""
    )

    optimization.optimized_bullets = optimized_bullets
    optimization.fabrication_flags = fabrication_flags

    resume_structured = resume.structured_data or {}
    try:
        pdf_path = await generate_pdf(str(optimization.id), resume_structured, optimized_bullets)
        optimization.output_file_path = pdf_path
    except Exception:
        pass

    await db.commit()
    await db.refresh(optimization)
    return optimization


@router.get("/optimizations/{optimization_id}/download")
async def download_optimized_pdf(
    optimization_id: uuid.UUID,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Optimization).where(
            Optimization.id == optimization_id,
            Optimization.user_id == token["user_id"],
        )
    )
    optimization = result.scalar_one_or_none()
    if not optimization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization not found")
    if not optimization.output_file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not yet generated")

    return FileResponse(
        optimization.output_file_path,
        media_type="application/pdf",
        filename=f"optimized_resume_{optimization_id}.pdf",
    )
