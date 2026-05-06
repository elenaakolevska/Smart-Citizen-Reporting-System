from fastapi import APIRouter, Depends

from app.schemas.user import CurrentUser, UserRole
from app.utils.dependencies import require_roles

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def admin_ping(current_user: CurrentUser = Depends(require_roles(UserRole.admin))) -> dict:
    """Admin-only route example (structure only)."""

    return {"status": "ok", "admin_user_id": str(current_user.id)}

