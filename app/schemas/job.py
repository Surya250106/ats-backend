from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import JobStatus


class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Title of the job posting")
    description: str = Field(..., min_length=5, description="Detailed job description")
    status: JobStatus = Field(JobStatus.OPEN, description="Status of the job posting")


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = Field(None, min_length=5)
    status: JobStatus | None = None


class JobResponse(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
