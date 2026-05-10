from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import CurrentUser, UserRead, UserRole, UserSettingsUpdate
from app.services import user_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserRead:
    """Return the current authenticated user including settings."""
    user = user_service.upsert_user(
        db,
        user_id=current_user.id,
        email=current_user.email,
    )
    return UserRead.from_orm_with_settings(user)


class RoleUpdate(BaseModel):
    role: UserRole


@router.patch("/me/role", response_model=UserRead)
def update_my_role(
    body: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserRead:
    """Update the current user's role (used by the frontend role-switcher)."""
    try:
        user = user_service.update_user_role(db, user_id=current_user.id, role=body.role)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.from_orm_with_settings(user)


@router.patch("/me/settings", response_model=UserRead)
def update_settings(
    settings_in: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserRead:
    """Update the current user's notification settings."""
    try:
        user = user_service.update_user_settings(
            db,
            user_id=current_user.id,
            email_notifications=settings_in.email_notifications,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.from_orm_with_settings(user)