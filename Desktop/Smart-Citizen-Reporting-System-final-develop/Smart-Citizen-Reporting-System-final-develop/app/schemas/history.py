from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_id: UUID
    old_status_id: int | None = None
    status_id: int | None = None
    created_at: datetime