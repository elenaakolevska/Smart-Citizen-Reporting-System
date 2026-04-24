from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import CurrentUser, UserRead, UserSettingsRead, UserSettingsUpdate
from app.services import user_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=CurrentUser)
def read_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Return the current authenticated user (decoded from Supabase JWT)."""
    return current_user


@router.post("/me", response_model=UserRead, status_code=200)
def upsert_me(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserRead:
    """
    Upsert the current user in the local DB.
    Call this on first login to ensure the user row exists.
    Returns the DB record.
    """
    user = user_service.upsert_user(
        db,
        user_id=current_user.id,
        email=current_user.email,
        role=current_user.role,
    )
    return UserRead.model_validate(user)


@router.get("/me/settings", response_model=UserSettingsRead)
def get_my_settings(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserSettingsRead:
    """Get the current user's preferences."""
    return user_service.get_user_settings(db, user_id=current_user.id)


@router.patch("/me/settings", response_model=UserSettingsRead)
def update_my_settings(
    settings_in: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserSettingsRead:
    """Update the current user's preferences."""
    return user_service.update_user_settings(db, user_id=current_user.id, settings_in=settings_in)
