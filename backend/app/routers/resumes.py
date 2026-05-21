import uuid
import os
import re
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import verify_token
from app.models.resume import Resume
from app.models.optimization import Optimization
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

    # Delete associated optimizations
    opt_rows = (await db.execute(select(Optimization).where(Optimization.resume_id == resume_id))).scalars().all()
    for o in opt_rows:
        if o.output_file_path and os.path.exists(o.output_file_path):
            os.remove(o.output_file_path)
        await db.delete(o)

    # Delete the file
    if resume.original_file_path and os.path.exists(resume.original_file_path):
        os.remove(resume.original_file_path)

    await db.delete(resume)
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
    except Exception:
        resume.structured_data = fallback_parse(resume.parsed_text)

    await db.commit()
    await db.refresh(resume)
    return resume


def fallback_parse(text: str) -> dict:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return {}

    structured: dict = {
        "full_name": None,
        "email": None,
        "phone": None,
        "location": None,
        "sections": [],
        "skills_detected": {"hard": [], "soft": []},
        "years_of_experience": None,
        "education": [],
    }

    for line in lines[:6]:
        if "@" in line and not structured["email"]:
            structured["email"] = line.strip()
        if re.match(r".*[\d]{3}.*[\d]{3}.*[\d]{4}", line) and not structured["phone"]:
            structured["phone"] = line.strip()

    section_keywords = [
        "experience", "employment", "work history", "professional experience",
        "education", "academic", "training",
        "skills", "technical skills", "clinical skills", "core competencies",
        "volunteer", "community", "service",
        "teaching", "academic appointments", "faculty",
        "membership", "affiliation", "professional society", "committee",
        "presentation", "publication", "research",
        "certification", "licensure", "license", "board",
        "award", "honor", "achievement",
        "language", "interest",
        "summary", "profile", "objective",
    ]

    current_section = {"title": "Summary", "bullets": []}

    for line in lines[1:]:
        line_lower = line.lower().rstrip(":").rstrip(".")

        is_header = False
        if line.isupper() and len(line) >= 5 and any(c.isalpha() and c.lower() in 'aeiou' for c in line):
            is_header = True
        elif line.endswith(":") and len(line) < 40:
            is_header = True
        else:
            for kw in section_keywords:
                if line_lower == kw or line_lower.rstrip("s") == kw:
                    is_header = True
                    break
                if kw.count(" ") >= 1 and line_lower.startswith(kw):
                    is_header = True
                    break

        if is_header:
            if current_section["bullets"]:
                structured["sections"].append(current_section)
            current_section = {"title": line.strip().rstrip(":"), "bullets": []}
        elif len(line) > 2:
            current_section["bullets"].append({"text": line, "is_quantified": False})

    if current_section["bullets"]:
        structured["sections"].append(current_section)

    return structured
