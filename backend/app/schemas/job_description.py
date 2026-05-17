import uuid
from datetime import datetime
from pydantic import BaseModel


class JDCreate(BaseModel):
    raw_text: str


class JDResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    company: str | None
    raw_text: str
    extracted_keywords: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JDListResponse(BaseModel):
    jds: list[JDResponse]
    total: int
