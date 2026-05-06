from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.sanitization import strip_html


class ReportBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=5000)
    latitude: float | None = None
    longitude: float | None = None

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        """Strip HTML tags to prevent XSS."""
        return strip_html(v)


class ReportCreate(ReportBase):
    """
    Schema used when creating a new report.
    Category and status are assigned later by the system,
    but the user can optionally suggest one.
    """
    category_id: int | None = None


class ReportUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    latitude: float | None = None
    longitude: float | None = None
    category_id: int | None = None
    status_id: int | None = None

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, v: str | None) -> str | None:
        """Strip HTML tags to prevent XSS."""
        if v is None:
            return None
        return strip_html(v)


class StatusUpdate(BaseModel):
    status_id: int


PriorityValue = Literal["Низок", "Среден", "Висок", "Итен"]


class PriorityUpdate(BaseModel):
    priority: PriorityValue


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)

    @field_validator("content", mode="before")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Strip HTML tags to prevent XSS."""
        return strip_html(v)


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

    id: UUID
    priority: str | None = None
    category_id: int | None = None
    status_id: int | None = None
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    possible_duplicate_of: UUID | None = None
    ai_confirmation_text: str | None = None
    history_entries: list[HistoryRead] = []
    comments: list[CommentRead] = []


class ReportExportParams(BaseModel):
    status: str | None = Field(default=None, description="Filter by status name")
    category: str | None = Field(default=None, description="Filter by category name")
    date_from: datetime | None = Field(default=None, description="Filter reports created on or after this date")
    date_to: datetime | None = Field(default=None, description="Filter reports created on or before this date")