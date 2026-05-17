import uuid
from datetime import datetime
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
    original_bullets: dict | None
    optimized_bullets: dict | None
    cover_letter_text: str | None
    output_file_path: str | None
    processing_time_ms: int | None
    model_used: str | None
    error_message: str | None
    fabrication_flags: dict | None
    credit_cost: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class OptimizationInitResponse(BaseModel):
    id: uuid.UUID
    status: str


class OptimizationListResponse(BaseModel):
    optimizations: list[OptimizationResponse]
    total: int
