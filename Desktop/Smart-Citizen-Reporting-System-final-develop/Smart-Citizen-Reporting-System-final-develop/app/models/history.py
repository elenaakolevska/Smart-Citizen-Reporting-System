from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.report import Report
    from app.models.status import Status
    from app.models.user import User


class History(Base):
    """
    Audit/history entry for a report.

    Typically created when a report changes status or gets reassigned.
    """

    __tablename__ = "history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    report_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )

    old_status_id: Mapped[int | None] = mapped_column(
        ForeignKey("statuses.id", ondelete="SET NULL"),
        nullable=True,
    )

    status_id: Mapped[int | None] = mapped_column(
        ForeignKey("statuses.id", ondelete="SET NULL"),
        nullable=True,
    )

    changed_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    report: Mapped[Report] = relationship(back_populates="history_entries")

    status: Mapped[Status | None] = relationship(
        back_populates="history_entries",
        foreign_keys="History.status_id",
    )

    old_status: Mapped[Status | None] = relationship(
        foreign_keys="History.old_status_id",
    )

    changed_by_user: Mapped[User | None] = relationship()
