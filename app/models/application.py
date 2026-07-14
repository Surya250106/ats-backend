import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    stage: Mapped[str] = mapped_column(
        String(50),
        default="Applied",
        index=True,
        nullable=False
    )
    resume_url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Prevent duplicate applications per job by the same candidate
    __table_args__ = (
        UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate"),
    )

    # Relationships
    job: Mapped["Job"] = relationship(  # type: ignore # noqa: F821
        "Job",
        back_populates="applications"
    )
    candidate: Mapped["User"] = relationship(  # type: ignore # noqa: F821
        "User",
        back_populates="applications"
    )
    history: Mapped[list["ApplicationHistory"]] = relationship(  # type: ignore # noqa: F821
        "ApplicationHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationHistory.changed_at.asc()"
    )
