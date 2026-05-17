import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    timezone: str
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountResponse(BaseModel):
    user: UserResponse
    tier: str
    tier_features: dict | None
    credits_used_this_month: int
    credits_limit: int | None
    subscription_status: str | None

    model_config = {"from_attributes": False}
