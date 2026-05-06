from pydantic import BaseModel, ConfigDict


class DepartmentCreate(BaseModel):
    name: str


class DepartmentRead(DepartmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int