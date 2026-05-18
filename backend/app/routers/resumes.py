import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import verify_token
from app.models.resume import Resume
from app.models.subscription import CreditUsage
from app.schemas.resume import ResumeResponse, ResumeUpdate, ResumeListResponse
from app.services.resume_parser import extract_text, parse_resume_text
from app.config import settings

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])

ALLOWED_TYPES = {"application/pdf": "pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx", "text/plain": "txt"}
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resume).where(Resume.user_id == token["user_id"], Resume.is_archived == False).order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()
    return ResumeListResponse(
        resumes=[ResumeResponse.model_validate(r) for r in resumes],
        total=len(resumes),
    )


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    token: dict = Depends(verify_token),
    file: UploadFile = File(...),
    title: str = Form("Untitled Resume"),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF, DOCX, and TXT files are accepted")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 5MB)")

    file_type = ALLOWED_TYPES[file.content_type]
    file_path = f"{settings.UPLOAD_DIR}/{uuid.uuid4()}.{file_type}"
    with open(file_path, "wb") as f:
        f.write(contents)

    raw_text = extract_text(file_path, file_type)

    resume = Resume(
        user_id=token["user_id"],
        title=title,
        original_file_path=file_path,
        parsed_text=raw_text,
        file_type=file_type,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == token["user_id"]))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: uuid.UUID,
    data: ResumeUpdate,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == token["user_id"]))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    if data.title is not None:
        resume.title = data.title
    if data.structured_data is not None:
        resume.structured_data = data.structured_data

    await db.commit()
    await db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: uuid.UUID,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == token["user_id"]))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    resume.is_archived = True
    await db.commit()


@router.post("/{resume_id}/reparse", response_model=ResumeResponse)
async def reparse_resume(
    resume_id: uuid.UUID,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == token["user_id"]))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No parsed text available")

    try:
        structured = await parse_resume_text(resume.parsed_text)
        resume.structured_data = structured
        await db.commit()
        await db.refresh(resume)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Parsing failed: {str(e)}")

    return resume
