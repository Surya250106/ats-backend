from sqlalchemy.orm import Session
from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def get_by_name(self, db: Session, name: str) -> Company | None:
        """Fetch a company by name."""
        return db.query(self.model).filter(self.model.name == name).first()


company_repository = CompanyRepository(Company)
