import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.history import ApplicationHistory
from app.models.job import Job
from app.models.user import User
from app.models.enums import UserRole
from app.repositories.application import application_repository
from app.repositories.job import job_repository
from app.schemas.application import ApplicationCreate, ApplicationStageUpdate
from app.workers.tasks import (
    send_application_submitted_email,
    send_recruiter_notification_email,
    send_stage_updated_email
)

# Valid stage transition state machine
VALID_TRANSITIONS = {
    "Applied": {"Screening", "Rejected"},
    "Screening": {"Interview", "Rejected"},
    "Interview": {"Offer", "Rejected"},
    "Offer": {"Hired", "Rejected"},
    "Hired": set(),
    "Rejected": set()
}


class ApplicationService:
    def apply_to_job(self, db: Session, job_id: uuid.UUID, app_in: ApplicationCreate, current_user: dict) -> Application:
        """
        Submits an application for a job on behalf of a candidate.
        Ensures candidates can apply to a job only once.
        Transactions wrap application and history creation, and roll back if any write fails.
        """
        candidate_id = uuid.UUID(current_user["sub"])

        # 1. Fetch Job
        job = job_repository.get(db, id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )

        # 2. Check if candidate already applied
        existing_app = application_repository.get_by_candidate_and_job(
            db, candidate_id=candidate_id, job_id=job_id
        )
        if existing_app:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied for this job"
            )

        # 3. Create Application & History inside a transaction
        db_app = Application(
            job_id=job_id,
            candidate_id=candidate_id,
            stage="Applied",
            resume_url=app_in.resume_url
        )

        try:
            db.add(db_app)
            db.flush()  # Populates db_app.id

            db_history = ApplicationHistory(
                application_id=db_app.id,
                previous_stage=None,
                new_stage="Applied",
                changed_by=candidate_id
            )
            db.add(db_history)
            db.commit()
            db.refresh(db_app)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit application: {str(e)}"
            )

        # 4. Enqueue Background Tasks after successful commit
        candidate_user = db.query(User).filter(User.id == candidate_id).first()
        candidate_email = candidate_user.email if candidate_user else "candidate@example.com"

        # Notify Candidate
        send_application_submitted_email.delay(candidate_email, job.title)

        # Notify recruiters for the company that posted the job
        recruiters = db.query(User).filter(
            User.company_id == job.company_id,
            User.role == UserRole.RECRUITER
        ).all()

        for recruiter in recruiters:
            send_recruiter_notification_email.delay(
                recruiter.email,
                candidate_email,
                job.title
            )

        return db_app

    def get_candidate_applications(self, db: Session, current_user: dict) -> list[Application]:
        """
        Retrieve all applications submitted by the current candidate.
        """
        candidate_id = uuid.UUID(current_user["sub"])
        return application_repository.get_by_candidate(db, candidate_id=candidate_id)

    def get_application_by_id(self, db: Session, id: uuid.UUID, current_user: dict) -> Application:
        """
        Retrieve an application by ID with ownership checks:
        - Candidates can only view their own applications.
        - Recruiters/Managers can only view applications for jobs inside their own company.
        """
        application = application_repository.get(db, id=id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )

        role = current_user.get("role")
        user_id = uuid.UUID(current_user["sub"])
        company_id_str = current_user.get("company_id")

        if role == UserRole.CANDIDATE:
            if application.candidate_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You can only view your own applications"
                )
        else:  # Recruiter / Hiring Manager
            if not company_id_str or application.job.company_id != uuid.UUID(company_id_str):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You can only view applications inside your own company"
                )

        return application

    def get_job_applications(self, db: Session, job_id: uuid.UUID, stage: str | None, current_user: dict) -> list[Application]:
        """
        Retrieve applications for a specific job. Enforces company access boundaries.
        """
        job = job_repository.get(db, id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )

        company_id_str = current_user.get("company_id")
        if not company_id_str or job.company_id != uuid.UUID(company_id_str):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only view applications inside your own company"
            )

        return application_repository.get_by_job(db, job_id=job_id, stage=stage)

    def update_stage(self, db: Session, id: uuid.UUID, stage_in: ApplicationStageUpdate, current_user: dict) -> Application:
        """
        Updates the stage of an application.
        - Enforces transition limits via the state machine.
        - Enforces ownership/company scope.
        - Wraps DB writes in a transaction and rolls back if an error occurs.
        """
        application = application_repository.get(db, id=id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )

        # 1. Authorize company membership
        company_id_str = current_user.get("company_id")
        if not company_id_str or application.job.company_id != uuid.UUID(company_id_str):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only manage applications belonging to your company"
            )

        # 2. State machine checks
        current_stage = application.stage
        new_stage = stage_in.stage

        allowed_next = VALID_TRANSITIONS.get(current_stage, set())
        if new_stage not in allowed_next:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stage transition from '{current_stage}' to '{new_stage}'"
            )

        # 3. DB Transaction Safety
        previous_stage = application.stage
        application.stage = new_stage

        db_history = ApplicationHistory(
            application_id=application.id,
            previous_stage=previous_stage,
            new_stage=new_stage,
            changed_by=uuid.UUID(current_user["sub"])
        )

        try:
            db.add(application)
            db.add(db_history)
            db.commit()
            db.refresh(application)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database update failed, stage transition rolled back: {str(e)}"
            )

        # 4. Enqueue background notification task
        candidate_email = application.candidate.email
        job_title = application.job.title
        send_stage_updated_email.delay(candidate_email, job_title, previous_stage, new_stage)

        return application


application_service = ApplicationService()
