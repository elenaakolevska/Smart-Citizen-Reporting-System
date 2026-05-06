from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.category import Category
from app.schemas.user import CurrentUser
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/")
def get_categories(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    return db.query(Category).all()