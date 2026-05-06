from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.notification import NotificationRead
from app.schemas.user import CurrentUser
from app.services import notification_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[NotificationRead]:
    """Get all notifications for the current user. Pass ?unread_only=true for badge count."""
    return notification_service.list_notifications(
        db, user_id=current_user.id, unread_only=unread_only
    )


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Returns { count: N } — use this for the notification bell badge."""
    count = notification_service.unread_count(db, user_id=current_user.id)
    return {"count": count}


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> NotificationRead:
    """Mark a single notification as read."""
    result = notification_service.mark_notification_read(
        db, notification_id=notification_id, user_id=current_user.id
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return result


@router.patch("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Mark all notifications as read for the current user."""
    updated = notification_service.mark_all_read(db, user_id=current_user.id)
    return {"marked_read": updated}