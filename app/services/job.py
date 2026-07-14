import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.enums import UserRole
from app.repositories.job import job_repository
from app.schemas.job import JobCreate, JobUpdate


class JobService:
    def create_job(self, db: Session, job_in: JobCreate, current_user: dict) -> Job:
        """
        Creates a new Job. Only recruiters can create jobs.
        The job's company_id is locked to the recruiter's company_id.
        """
        company_id_str = current_user.get("company_id")
        if not company_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recruiter user must belong to a company to create jobs"
            )

        db_job = Job(
            title=job_in.title,
            description=job_in.description,
            status=job_in.status,
            company_id=uuid.UUID(company_id_str),
            created_by=uuid.UUID(current_user["sub"])
        )
        return job_repository.create(db, obj_in=db_job)

    def get_jobs(self, db: Session, current_user: dict) -> list[Job]:
        """
        Fetch jobs.
        Candidates see all open jobs.
        Recruiters and Hiring Managers only see jobs in their own company.
        """
        role = current_user.get("role")
        if role == UserRole.CANDIDATE:
            return job_repository.get_all_open(db)

        company_id_str = current_user.get("company_id")
        if not company_id_str:
            return []

        return job_repository.get_by_company(db, company_id=uuid.UUID(company_id_str))

    def get_job_by_id(self, db: Session, id: uuid.UUID) -> Job:
        """
        Retrieve a single job by ID. Raises 404 if not found.
        """
        job = job_repository.get(db, id=id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        return job

    def update_job(self, db: Session, id: uuid.UUID, job_in: JobUpdate, current_user: dict) -> Job:
        """
        Updates a job posting.
        Validates that the recruiter belongs to the company that posted the job.
        """
        job = self.get_job_by_id(db, id=id)

        company_id_str = current_user.get("company_id")
        if not company_id_str or job.company_id != uuid.UUID(company_id_str):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only manage jobs belonging to your own company"
            )

        return job_repository.update(db, db_obj=job, obj_in=job_in)

    def delete_job(self, db: Session, id: uuid.UUID, current_user: dict) -> Job:
        """
        Deletes a job posting.
        Validates that the recruiter belongs to the company that posted the job.
        """
        job = self.get_job_by_id(db, id=id)

        company_id_str = current_user.get("company_id")
        if not company_id_str or job.company_id != uuid.UUID(company_id_str):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only manage jobs belonging to your own company"
            )

        return job_repository.remove(db, id=id)


job_service = JobService()
