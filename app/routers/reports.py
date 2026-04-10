from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import ReportCreate, ReportRead
from app.schemas.user import CurrentUser, UserRole
from app.services import report_service
from app.utils.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportRead, status_code=201)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.citizen, UserRole.admin)),
) -> ReportRead:
    """
    Create a citizen report.
    """
    return report_service.create_report(db, report_in=report_in, current_user=current_user)


@router.get("", response_model=list[ReportRead])
def list_reports(
    page: int = 1,
    page_size: int = 10,
    status_id: int | None = None,
    category_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[ReportRead]:
    """
    List reports with:
    - RBAC (citizen sees only own)
    - pagination
    - filters
    """
    return report_service.list_reports(
        db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_id=status_id,
        category_id=category_id,
    )


@router.get("/{report_id}", response_model=ReportRead)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportRead:
    """
    Fetch single report with RBAC check
    """
    return report_service.get_report(db, report_id=report_id, current_user=current_user)