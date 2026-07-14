from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def get_by_email(self, db: Session, email: str) -> User | None:
        """Fetch user by unique email address."""
        return db.query(self.model).filter(self.model.email == email).first()


user_repository = UserRepository(User)
