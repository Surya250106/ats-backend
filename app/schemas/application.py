from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ApplicationCreate(BaseModel):
    resume_url: str | None = Field(None, max_length=1024, description="URL of candidate resume")


class ApplicationStageUpdate(BaseModel):
    stage: str = Field(..., min_length=2, max_length=50, description="New stage to transition the application to")


class ApplicationHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    previous_stage: str | None
    new_stage: str
    changed_by: uuid.UUID
    changed_at: datetime


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    stage: str
    resume_url: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationDetailResponse(ApplicationResponse):
    history: list[ApplicationHistoryResponse] = []
