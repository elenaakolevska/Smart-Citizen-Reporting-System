from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.attachment import Attachment
    from app.models.category import Category
    from app.models.comment import Comment
    from app.models.department import Department
    from app.models.history import History
    from app.models.status import Status
    from app.models.user import User


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str | None] = mapped_column(String(50), nullable=True)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True,
    )
    status_id: Mapped[int | None] = mapped_column(
        ForeignKey("statuses.id", ondelete="SET NULL"), nullable=True,
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True,
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

    possible_duplicate_of: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("reports.id", ondelete="SET NULL"), nullable=True,
    )

    # AI - generated confirmation text in Macedonian
    ai_confirmation_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Citizen rating (CR-06)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="reports")
    category: Mapped[Category | None] = relationship(back_populates="reports")
    status: Mapped[Status | None] = relationship(back_populates="reports")
    department: Mapped[Department | None] = relationship(back_populates="reports")
    attachments: Mapped[list[Attachment]] = relationship(back_populates="report", cascade="all, delete-orphan")
    comments: Mapped[list[Comment]] = relationship(back_populates="report", cascade="all, delete-orphan")
    history_entries: Mapped[list[History]] = relationship(back_populates="report", cascade="all, delete-orphan")