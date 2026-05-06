from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID
    report_id: UUID
    message: str
    is_read: bool
    created_at: datetime


class NotificationMarkRead(BaseModel):
    ids: list[int]