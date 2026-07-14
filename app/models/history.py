import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ApplicationHistory(Base):
    __tablename__ = "application_histories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    previous_stage: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    new_stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    changed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    application: Mapped["Application"] = relationship(  # type: ignore # noqa: F821
        "Application",
        back_populates="history"
    )
    changer: Mapped["User"] = relationship(  # type: ignore # noqa: F821
        "User"
    )
