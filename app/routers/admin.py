from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import CurrentUser, UserRead, UserRole
from app.services import user_service
from app.utils.dependencies import require_roles

router = APIRouter(prefix="/admin", tags=["admin"])


class RoleUpdate(BaseModel):
    role: UserRole


@router.get("/ping")
def admin_ping(current_user: CurrentUser = Depends(require_roles(UserRole.admin))) -> dict:
    """Admin-only route example (structure only)."""
    return {"status": "ok", "admin_user_id": str(current_user.id)}


@router.patch("/users/{user_id}/role", response_model=UserRead)
def set_user_role(
    user_id: UUID,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.admin)),
) -> UserRead:
    """Set a user's role. Admin only."""
    try:
        user = user_service.update_user_role(db, user_id=user_id, role=body.role)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.from_orm_with_settings(user)
