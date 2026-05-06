from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.report import Report
    from app.models.user import User


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("report_id", name="uq_ratings_report_id"),
        CheckConstraint("stars BETWEEN 1 AND 5", name="ck_ratings_stars_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    report_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    citizen_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    report: Mapped[Report] = relationship()
    citizen: Mapped[User] = relationship()
