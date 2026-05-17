import uuid
from datetime import datetime
from pydantic import BaseModel


class ResumeSection(BaseModel):
    title: str
    bullets: list[dict]


class ResumeStructuredData(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    sections: list[ResumeSection] = []
    skills_detected: dict | None = None
    years_of_experience: float | None = None
    education: list[dict] = []


class ResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    file_type: str | None
    structured_data: dict | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeUpdate(BaseModel):
    title: str | None = None
    structured_data: dict | None = None


class ResumeListResponse(BaseModel):
    resumes: list[ResumeResponse]
    total: int
