from __future__ import annotations
import json
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.security import verify_supabase_token
from app.db.session import get_db
from app.schemas.user import CurrentUser, UserRole
from app.services import user_service

bearer_scheme = HTTPBearer(auto_error=False)

DEV_USER = CurrentUser(
    id=UUID("12345678-1234-1234-1234-123456789012"),
    email="dev@example.com",
    role=UserRole.admin,
)


def get_current_user_logic(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """
    Extract and verify the current user from a Supabase-issued JWT.
    On first login, automatically creates the user row in the local DB (upsert).
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    token = credentials.credentials
    payload = verify_supabase_token(token)

    try:
        user_id = UUID(str(payload["sub"]))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload (`sub` must be a UUID).",
        )

    email = payload.get("email")
    raw_role = payload.get("app_role") or payload.get("role") or UserRole.citizen.value
    try:
        role = UserRole(str(raw_role))
    except Exception:
        role = UserRole.citizen

    db.execute(
        text("select set_config('request.jwt.claim.sub', :sub, true)"),
        {"sub": str(user_id)},
    )
    db.execute(
        text("select set_config('request.jwt.claim.role', :role, true)"),
        {"role": role.value},
    )
    db.execute(
        text("select set_config('request.jwt.claims', :claims, true)"),
        {
            "claims": json.dumps(
                {
                    "sub": str(user_id),
                    "email": email,
                    "role": role.value,
                    "app_role": role.value,
                }
            )
        },
    )

    # ✅ BE2: Upsert — создај корисник во DB ако не постои
    user_service.upsert_user(db, user_id=user_id, email=email, role=role)

    return CurrentUser(id=user_id, email=email, role=role)


def require_roles(*allowed_roles: UserRole):
    """Dependency factory for role-based access control."""
    def _role_dependency(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions.",
            )
        return current_user
    return _role_dependency

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    from app.core.config import get_settings
    settings = get_settings()
    if settings.dev_skip_auth:
        return DEV_USER
    return get_current_user_logic(credentials, db)
