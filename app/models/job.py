import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import JobStatus


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, name="jobstatus", values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.OPEN,
        nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship(  # type: ignore # noqa: F821
        "Company",
        back_populates="jobs"
    )
    creator: Mapped["User"] = relationship(  # type: ignore # noqa: F821
        "User",
        back_populates="created_jobs"
    )
    applications: Mapped[list["Application"]] = relationship(  # type: ignore # noqa: F821
        "Application",
        back_populates="job",
        cascade="all, delete-orphan"
    )
