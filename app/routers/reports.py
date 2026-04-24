from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.attachment import AttachmentRead
from app.schemas.report import (
    CommentCreate,
    CommentRead,
    ReportCreate,
    ReportRead,
    ReportRating,
    ReportUpdate,
    StatusUpdate,
)
from app.schemas.user import CurrentUser, UserRole
from app.services import report_service
from app.utils.dependencies import get_current_user, require_roles
from app.utils.file_upload import save_upload

router = APIRouter(prefix="/reports", tags=["reports"])


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@router.post("", response_model=ReportRead, status_code=201)
def create_report(
    report_in: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.citizen, UserRole.admin)),
) -> ReportRead:
    """Create a citizen report. Only citizens and admins may submit reports."""
    report = report_service.create_report(db, report_in=report_in, current_user=current_user)
    background_tasks.add_task(report_service.run_report_ai_pipeline, report.id)
    return report


@router.get("", response_model=list[ReportRead])
def list_reports(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[ReportRead]:
    """Citizens see only their own. Officers and admins see all."""
    return report_service.list_reports(db, current_user=current_user)


@router.get("/{report_id}", response_model=ReportRead)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportRead:
    """Get a single report by ID. Citizens can only fetch their own."""
    return report_service.get_report(db, report_id=report_id, current_user=current_user)


@router.patch("/{report_id}", response_model=ReportRead)
def update_report(
    report_id: int,
    report_in: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportRead:
    """Citizens update their own only. Officers/admins update any."""
    return report_service.update_report(db, report_id=report_id, report_in=report_in, current_user=current_user)


@router.patch("/{report_id}/status", response_model=ReportRead)
def update_report_status(
    report_id: int,
    status_in: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> ReportRead:
    """Change a report's status. Officers and admins only. Always logs history."""
    return report_service.update_status(db, report_id=report_id, status_in=status_in, current_user=current_user)


@router.post("/{report_id}/rate", response_model=ReportRead)
def rate_report(
    report_id: int,
    rating_in: ReportRating,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportRead:
    """Rate a closed report. Citizens only for their own reports."""
    return report_service.rate_report(db, report_id=report_id, rating_in=rating_in, current_user=current_user)


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """Delete a report. Citizens can only delete their own; admins can delete any."""
    report_service.delete_report(db, report_id=report_id, current_user=current_user)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

@router.get("/{report_id}/comments", response_model=list[CommentRead])
def list_comments(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[CommentRead]:
    """Get all comments on a report. Citizens can only view their own reports' comments."""
    return report_service.list_comments(db, report_id=report_id, current_user=current_user)


@router.post("/{report_id}/comments", response_model=CommentRead, status_code=201)
def create_comment(
    report_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> CommentRead:
    """Add a comment. Officers and admins only. Triggers notification to report owner."""
    return report_service.create_comment(db, report_id=report_id, comment_in=comment_in, current_user=current_user)


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

@router.get("/{report_id}/attachments", response_model=list[AttachmentRead])
def list_attachments(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[AttachmentRead]:
    """Get all attachments on a report. Citizens can only view their own reports'."""
    return report_service.list_attachments(db, report_id=report_id, current_user=current_user)


@router.post("/{report_id}/attachments", response_model=AttachmentRead, status_code=201)
async def upload_attachment(
    report_id: int,
    file: UploadFile = File(..., description="JPG, PNG or PDF. Max 5 MB."),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> AttachmentRead:
    """Upload evidence to a report. Officers and admins only. Validates type and size."""
    file_url, file_size_bytes = await save_upload(file)
    return report_service.create_attachment(
        db,
        report_id=report_id,
        file_url=file_url,
        original_filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        file_size_bytes=file_size_bytes,
        current_user=current_user,
    )