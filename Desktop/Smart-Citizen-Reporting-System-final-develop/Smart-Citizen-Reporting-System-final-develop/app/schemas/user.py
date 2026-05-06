from __future__ import annotations

import enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRole(str, enum.Enum):
    citizen = "citizen"
    officer = "officer"
    admin = "admin"


class UserRead(BaseModel):
    """
    User schema for API responses (backed by DB model in a real implementation).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole


class CurrentUser(BaseModel):
    """
    User info extracted from a Supabase JWT (mocked in this template).

    This may not necessarily exist in the local DB yet.
    """

    id: UUID
    email: EmailStr | None = None
    role: UserRole = UserRole.citizen

