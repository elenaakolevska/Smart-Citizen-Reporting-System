from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.schemas.user import UserSettingsUpdate, UserSettingsRead


def upsert_user(
    db: Session,
    *,
    user_id: UUID,
    email: str | None,
    role: UserRole,
) -> User:
    user = db.get(User, user_id)

    if user is None:
        user = User(
            id=user_id,
            email=email or f"{user_id}@unknown.local",
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def get_user_settings(db: Session, *, user_id: UUID) -> UserSettingsRead:
    user = db.get(User, user_id)
    if not user:
        return UserSettingsRead(email_notifications=True)
    return UserSettingsRead(email_notifications=user.email_notifications_enabled)


def update_user_settings(
    db: Session, *, user_id: UUID, settings_in: UserSettingsUpdate
) -> UserSettingsRead:
    user = db.get(User, user_id)
    if not user:
        user = User(id=user_id, email=f"{user_id}@unknown.local")
        db.add(user)

    user.email_notifications_enabled = settings_in.email_notifications
    db.commit()
    return UserSettingsRead(email_notifications=user.email_notifications_enabled)
