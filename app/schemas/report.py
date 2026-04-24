from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=5000)
    latitude: float | None = None
    longitude: float | None = None


class ReportCreate(ReportBase):
    title: str | None = None
    """
    Schema used when creating a new report.
    Category and status are assigned later by the system,
    but the user can optionally suggest one.
    """
    category_id: int | None = None
    priority: str | None = None


class ReportUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    latitude: float | None = None
    longitude: float | None = None
    category_id: int | None = None
    status_id: int | None = None
    priority: str | None = None


class ReportRating(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    rating_comment: str | None = Field(default=None, max_length=1000)


class StatusUpdate(BaseModel):
    status_id: int


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentRead(BaseModel):
    """Schema returned for report comments."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID
    content: str
    created_at: datetime


class HistoryRead(BaseModel):
    """Schema returned for report history entries."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    old_status_id: int | None = None
    status_id: int | None = None
    changed_by_user_id: UUID | None = None
    created_at: datetime


class ReportRead(ReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None = None
    priority: str | None = None
    category_id: int | None = None
    status_id: int | None = None
    department_id: int | None = None
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    possible_duplicate_of: int | None = None
    ai_confirmation_text: str | None = None
    rating: int | None = None
    rating_comment: str | None = None
    history_entries: list[HistoryRead] = []
    comments: list[CommentRead] = []
