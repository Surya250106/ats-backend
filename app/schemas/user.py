from datetime import datetime
import uuid
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, description="Plain text password")
    company_id: uuid.UUID | None = Field(None, description="Join an existing company")
    company_name: str | None = Field(None, description="Create a new company on registration (recruiters/managers only)")


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID | None
    created_at: datetime
