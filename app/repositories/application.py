import uuid
from sqlalchemy.orm import Session
from app.models.application import Application
from app.models.job import Job
from app.models.history import ApplicationHistory
from app.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):
    def get_by_candidate(self, db: Session, candidate_id: uuid.UUID) -> list[Application]:
        """Fetch all applications submitted by a specific candidate."""
        return db.query(self.model).filter(self.model.candidate_id == candidate_id).all()

    def get_by_company(self, db: Session, company_id: uuid.UUID) -> list[Application]:
        """Fetch all applications for jobs belonging to a specific company."""
        return (
            db.query(self.model)
            .join(Job)
            .filter(Job.company_id == company_id)
            .all()
        )

    def get_by_job(self, db: Session, job_id: uuid.UUID, stage: str | None = None) -> list[Application]:
        """Fetch all applications for a specific job, with optional stage filtering."""
        query = db.query(self.model).filter(self.model.job_id == job_id)
        if stage:
            query = query.filter(self.model.stage == stage)
        return query.all()

    def get_by_candidate_and_job(self, db: Session, candidate_id: uuid.UUID, job_id: uuid.UUID) -> Application | None:
        """Fetch application for a candidate and job (useful for preventing duplicate applies)."""
        return (
            db.query(self.model)
            .filter(self.model.candidate_id == candidate_id, self.model.job_id == job_id)
            .first()
        )

    def create_history(self, db: Session, *, history_obj: ApplicationHistory) -> ApplicationHistory:
        """Insert a stage transition history record."""
        db.add(history_obj)
        db.commit()
        db.refresh(history_obj)
        return history_obj


application_repository = ApplicationRepository(Application)
