from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_id: UUID
    user_id: UUID
    content: str
    created_at: datetime