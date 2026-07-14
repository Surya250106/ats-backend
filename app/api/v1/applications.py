import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.schemas.application import (
    ApplicationCreate,
    ApplicationStageUpdate,
    ApplicationResponse,
    ApplicationDetailResponse
)
from app.services.application import application_service

# Router for '/applications' prefix
router = APIRouter(prefix="/applications", tags=["Applications"])

# Router for '/jobs' prefix to support nested application endpoints
jobs_applications_router = APIRouter(prefix="/jobs", tags=["Applications"])


@jobs_applications_router.post("/{job_id}/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_to_job(
    job_id: uuid.UUID,
    app_in: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("candidate"))
) -> ApplicationResponse:
    """
    Apply to a job listing. Only candidates can apply, and only once per job.
    """
    return application_service.apply_to_job(db, job_id, app_in, current_user)


@router.get("/me", response_model=list[ApplicationResponse], status_code=status.HTTP_200_OK)
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("candidate"))
) -> list[ApplicationResponse]:
    """
    View own applications list. Only accessible by candidates.
    """
    return application_service.get_candidate_applications(db, current_user)


@router.get("/{id}", response_model=ApplicationDetailResponse, status_code=status.HTTP_200_OK)
def get_application(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> ApplicationDetailResponse:
    """
    Get detailed application by ID (including history).
    - Candidates can only view their own applications.
    - Recruiters/Managers can only view applications inside their own company.
    """
    return application_service.get_application_by_id(db, id, current_user)


@jobs_applications_router.get("/{job_id}/applications", response_model=list[ApplicationResponse], status_code=status.HTTP_200_OK)
def get_job_applications(
    job_id: uuid.UUID,
    stage: str | None = Query(None, description="Filter applications by stage"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("recruiter", "hiring_manager"))
) -> list[ApplicationResponse]:
    """
    List all applications for a specific job. Supported by ?stage= parameter.
    Only recruiters and hiring managers of the owning company have access.
    """
    return application_service.get_job_applications(db, job_id, stage, current_user)


@router.put("/{id}/stage", response_model=ApplicationResponse, status_code=status.HTTP_200_OK)
def update_application_stage(
    id: uuid.UUID,
    stage_in: ApplicationStageUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("recruiter", "hiring_manager"))
) -> ApplicationResponse:
    """
    Update the stage of a job application.
    Enforces the stage transition state machine rules.
    Only recruiters and hiring managers of the owning company have access.
    """
    return application_service.update_stage(db, id, stage_in, current_user)
