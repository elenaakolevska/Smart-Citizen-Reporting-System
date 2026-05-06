from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.attachment import Attachment
    from app.models.category import Category
    from app.models.comment import Comment
    from app.models.history import History
    from app.models.status import Status
    from app.models.user import User


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str | None] = mapped_column(String(50), nullable=True)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True,
    )
    status_id: Mapped[int | None] = mapped_column(
        ForeignKey("statuses.id", ondelete="SET NULL"), nullable=True,
    )
    
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    possible_duplicate_of: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True,
    )

    # AI - generated confirmation text in Macedonian
    ai_confirmation_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="reports")
    category: Mapped[Category | None] = relationship(back_populates="reports")
    status: Mapped[Status | None] = relationship(back_populates="reports")
    attachments: Mapped[list[Attachment]] = relationship(back_populates="report", cascade="all, delete-orphan")
    comments: Mapped[list[Comment]] = relationship(back_populates="report", cascade="all, delete-orphan")
    history_entries: Mapped[list[History]] = relationship(back_populates="report", cascade="all, delete-orphan")
