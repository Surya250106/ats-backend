import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.services.job import job_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("recruiter"))
) -> JobResponse:
    """
    Create a new job posting. Only accessible by recruiters.
    """
    return job_service.create_job(db, job_in, current_user)


@router.get("", response_model=list[JobResponse], status_code=status.HTTP_200_OK)
def get_jobs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> list[JobResponse]:
    """
    Fetch jobs.
    - Candidates see all open jobs.
    - Recruiters and Hiring Managers see jobs in their own company.
    """
    return job_service.get_jobs(db, current_user)


@router.get("/{id}", response_model=JobResponse, status_code=status.HTTP_200_OK)
def get_job(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> JobResponse:
    """
    Fetch a single job posting by ID.
    """
    return job_service.get_job_by_id(db, id)


@router.put("/{id}", response_model=JobResponse, status_code=status.HTTP_200_OK)
def update_job(
    id: uuid.UUID,
    job_in: JobUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("recruiter"))
) -> JobResponse:
    """
    Update a job posting. Only accessible by recruiters belonging to the job's company.
    """
    return job_service.update_job(db, id, job_in, current_user)


@router.delete("/{id}", response_model=JobResponse, status_code=status.HTTP_200_OK)
def delete_job(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("recruiter"))
) -> JobResponse:
    """
    Delete a job posting. Only accessible by recruiters belonging to the job's company.
    """
    return job_service.delete_job(db, id, current_user)
