from pydantic import BaseModel, ConfigDict


class StatusCreate(BaseModel):
    name: str


class StatusRead(StatusCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int