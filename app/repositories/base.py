from typing import Generic, Type, TypeVar, Any
import uuid
from sqlalchemy.orm import Session
from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic Base Repository that provides standard CRUD methods.
    """
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: uuid.UUID) -> ModelType | None:
        """Fetch a single record by ID."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Fetch multiple records with offset pagination."""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: Any) -> ModelType:
        """Create a new record."""
        if isinstance(obj_in, self.model):
            db.add(obj_in)
            db.commit()
            db.refresh(obj_in)
            return obj_in

        db_obj = self.model(**(obj_in if isinstance(obj_in, dict) else obj_in.model_dump()))
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: ModelType, obj_in: Any) -> ModelType:
        """Update an existing record."""
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: uuid.UUID) -> ModelType | None:
        """Delete a record by ID."""
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj
