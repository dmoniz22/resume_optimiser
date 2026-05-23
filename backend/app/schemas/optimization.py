import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class OptimizationRequest(BaseModel):
    resume_id: uuid.UUID
    jd_id: uuid.UUID


class OptimizationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_id: uuid.UUID
    jd_id: uuid.UUID
    status: str
    pre_score: float | None
    post_score: float | None
    original_bullets: Any | None = None
    optimized_bullets: Any | None = None
    cover_letter_text: str | None
    output_file_path: str | None
    processing_time_ms: int | None
    model_used: str | None
    error_message: str | None
    fabrication_flags: Any | None = None
    credit_cost: int
    template: str = "modern"
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class OptimizationUpdate(BaseModel):
    optimized_bullets: list[dict] | None = None
    template: str | None = None


class OptimizationInitResponse(BaseModel):
    id: uuid.UUID
    status: str


class OptimizationListResponse(BaseModel):
    optimizations: list[OptimizationResponse]
    total: int
