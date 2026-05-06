from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.user import User, UserRole


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

    changed = False
    next_email = email or user.email
    if user.email != next_email:
        user.email = next_email
        changed = True

    if user.role != role:
        user.role = role
        changed = True

    if changed:
        db.commit()
        db.refresh(user)

    return user