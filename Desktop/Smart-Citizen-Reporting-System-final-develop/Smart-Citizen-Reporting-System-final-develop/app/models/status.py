from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.history import History
    from app.models.report import Report


class Status(Base):
    __tablename__ = "statuses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )

    reports: Mapped[list[Report]] = relationship(back_populates="status")

    history_entries: Mapped[list[History]] = relationship(
        back_populates="status",
        foreign_keys="History.status_id",
    )
