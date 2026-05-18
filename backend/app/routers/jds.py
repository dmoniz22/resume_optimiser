import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import verify_token
from app.models.job_description import JobDescription
from app.schemas.job_description import JDCreate, JDResponse, JDListResponse
from app.services.jd_extractor import extract_jd_keywords

router = APIRouter(prefix="/api/v1/jds", tags=["job_descriptions"])


@router.post("", response_model=JDResponse, status_code=status.HTTP_201_CREATED)
async def create_jd(
    data: JDCreate,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    jd = JobDescription(
        user_id=token["user_id"],
        raw_text=data.raw_text,
    )
    db.add(jd)
    await db.commit()
    await db.refresh(jd)

    try:
        keywords = await extract_jd_keywords(data.raw_text)
        jd.title = keywords.get("job_title")
        jd.company = keywords.get("company_name")
        jd.extracted_keywords = keywords
        await db.commit()
        await db.refresh(jd)
    except Exception:
        pass

    return jd


@router.get("", response_model=JDListResponse)
async def list_jds(
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JobDescription).where(JobDescription.user_id == token["user_id"]).order_by(JobDescription.created_at.desc())
    )
    jds = result.scalars().all()
    return JDListResponse(
        jds=[JDResponse.model_validate(j) for j in jds],
        total=len(jds),
    )


@router.get("/{jd_id}", response_model=JDResponse)
async def get_jd(
    jd_id: uuid.UUID,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(JobDescription).where(JobDescription.id == jd_id, JobDescription.user_id == token["user_id"]))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")
    return jd


@router.delete("/{jd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_jd(
    jd_id: uuid.UUID,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(JobDescription).where(JobDescription.id == jd_id, JobDescription.user_id == token["user_id"]))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    await db.delete(jd)
    await db.commit()
