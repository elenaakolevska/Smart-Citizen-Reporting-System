from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.status import Status
from app.schemas.user import CurrentUser
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/statuses", tags=["Statuses"])

@router.get("/")
def get_statuses(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    return db.query(Status).all()