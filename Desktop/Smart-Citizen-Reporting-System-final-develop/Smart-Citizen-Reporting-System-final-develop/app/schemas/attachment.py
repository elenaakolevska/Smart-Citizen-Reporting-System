from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: UUID
    file_url: str
    original_filename: str
    content_type: str
    file_size_bytes: int
    created_at: datetime