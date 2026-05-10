from __future__ import annotations

import enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRole(str, enum.Enum):
    citizen = "citizen"
    officer = "officer"
    admin = "admin"


class UserSettings(BaseModel):
    email_notifications: bool = True


class UserRead(BaseModel):
    """
    User schema for API responses (backed by DB model in a real implementation).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None = None
    role: UserRole
    settings: UserSettings = UserSettings()

    @classmethod
    def from_orm_with_settings(cls, user: object) -> "UserRead":
        return cls(
            id=getattr(user, "id"),
            email=getattr(user, "email"),
            full_name=getattr(user, "full_name", None),
            role=getattr(user, "role"),
            settings=UserSettings(
                email_notifications=getattr(user, "email_notifications", True)
            ),
        )


class UserSettingsUpdate(BaseModel):
    email_notifications: bool


class CurrentUser(BaseModel):
    """
    User info extracted from a Supabase JWT (mocked in this template).

    This may not necessarily exist in the local DB yet.
    """

    id: UUID
    email: EmailStr | None = None
    role: UserRole = UserRole.citizen

