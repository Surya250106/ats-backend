import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(  # type: ignore # noqa: F821
        "User",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(  # type: ignore # noqa: F821
        "Job",
        back_populates="company",
        cascade="all, delete-orphan"
    )
