import uuid
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.enums import JobStatus
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def get_by_company(self, db: Session, company_id: uuid.UUID) -> list[Job]:
        """Fetch all jobs belonging to a specific company."""
        return db.query(self.model).filter(self.model.company_id == company_id).all()

    def get_all_open(self, db: Session) -> list[Job]:
        """Fetch all open jobs."""
        return db.query(self.model).filter(self.model.status == JobStatus.OPEN).all()


job_repository = JobRepository(Job)
