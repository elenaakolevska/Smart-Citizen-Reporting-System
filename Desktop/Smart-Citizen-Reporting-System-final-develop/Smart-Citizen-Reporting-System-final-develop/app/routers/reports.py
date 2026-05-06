from datetime import datetime
from io import BytesIO, StringIO
from uuid import UUID
import csv

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.attachment import AttachmentRead
from app.schemas.rating import RatingCreate, RatingRead
from app.schemas.report import (
    CommentCreate,
    CommentRead,
    PriorityUpdate,
    ReportCreate,
    ReportRead,
    ReportUpdate,
    StatusUpdate,
)
from app.schemas.user import CurrentUser, UserRole
from app.services import rating_service, report_service
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
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportRead:
    """Get a single report by ID. Citizens can only fetch their own."""
    return report_service.get_report(db, report_id=report_id, current_user=current_user)


@router.patch("/{report_id}", response_model=ReportRead)
def update_report(
    report_id: UUID,
    report_in: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportRead:
    """Citizens update their own only. Officers/admins update any."""
    return report_service.update_report(db, report_id=report_id, report_in=report_in, current_user=current_user)


@router.patch("/{report_id}/status", response_model=ReportRead)
def update_report_status(
    report_id: UUID,
    status_in: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> ReportRead:
    """Change a report's status. Officers and admins only. Always logs history."""
    return report_service.update_status(db, report_id=report_id, status_in=status_in, current_user=current_user)


@router.patch("/{report_id}/priority", response_model=ReportRead)
def update_report_priority(
    report_id: UUID,
    priority_in: PriorityUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> ReportRead:
    """Change a report's priority. Officers and admins only."""
    return report_service.update_priority(
        db,
        report_id=report_id,
        priority_in=priority_in,
        current_user=current_user,
    )


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: UUID,
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
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[CommentRead]:
    """Get all comments on a report. Citizens can only view their own reports' comments."""
    return report_service.list_comments(db, report_id=report_id, current_user=current_user)


@router.post("/{report_id}/comments", response_model=CommentRead, status_code=201)
def create_comment(
    report_id: UUID,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> CommentRead:
    """Add a comment. Officers and admins only. Triggers notification to report owner."""
    return report_service.create_comment(db, report_id=report_id, comment_in=comment_in, current_user=current_user)


# ---------------------------------------------------------------------------
# Ratings (CR-06) — citizen rates their own closed report; one rating per report
# ---------------------------------------------------------------------------

@router.post("/{report_id}/rating", response_model=RatingRead, status_code=201)
def create_rating(
    report_id: UUID,
    rating_in: RatingCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.citizen)),
) -> RatingRead:
    """Citizen leaves a 1–5 star rating on their own closed report. Only once."""
    return rating_service.create_rating(
        db, report_id=report_id, rating_in=rating_in, current_user=current_user
    )


@router.get("/{report_id}/rating", response_model=RatingRead)
def get_rating(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> RatingRead:
    """Read the rating for a report. Citizens may only read ratings on their own reports."""
    return rating_service.get_rating(db, report_id=report_id, current_user=current_user)


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

@router.get("/{report_id}/attachments", response_model=list[AttachmentRead])
def list_attachments(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[AttachmentRead]:
    """Get all attachments on a report. Citizens can only view their own reports'."""
    return report_service.list_attachments(db, report_id=report_id, current_user=current_user)


@router.post("/{report_id}/attachments", response_model=AttachmentRead, status_code=201)
async def upload_attachment(
    report_id: UUID,
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


# ---------------------------------------------------------------------------
# Export (FR-08) — officer/admin only
# ---------------------------------------------------------------------------

_EXPORT_COLUMNS = [
    ("ID",          lambda r: str(r.id)),
    ("Description", lambda r: r.description),
    ("Category",    lambda r: r.category.name if r.category else ""),
    ("Status",      lambda r: r.status.name if r.status else ""),
    ("Priority",    lambda r: r.priority or ""),
    ("Latitude",    lambda r: "" if r.latitude is None else r.latitude),
    ("Longitude",   lambda r: "" if r.longitude is None else r.longitude),
    ("Created at",  lambda r: r.created_at.isoformat() if r.created_at else ""),
    ("Updated at",  lambda r: r.updated_at.isoformat() if r.updated_at else ""),
    ("User ID",     lambda r: str(r.user_id)),
]


def _export_filename(prefix: str, ext: str) -> str:
    return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.{ext}"


@router.get("/export/csv")
def export_reports_csv(
    status: str | None = Query(default=None, description="Filter by status name"),
    category: str | None = Query(default=None, description="Filter by category name"),
    date_from: datetime | None = Query(default=None, description="Filter reports created on or after this datetime"),
    date_to: datetime | None = Query(default=None, description="Filter reports created on or before this datetime"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> StreamingResponse:
    """Stream filtered reports as CSV. Officer/admin only. (FR-08)"""
    reports = report_service.export_reports(
        db, status=status, category=category, date_from=date_from, date_to=date_to,
    )

    headers = [label for label, _ in _EXPORT_COLUMNS]
    extractors = [extractor for _, extractor in _EXPORT_COLUMNS]

    def _iter_csv():
        # UTF-8 BOM so Excel renders Cyrillic correctly.
        yield "﻿"
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(headers)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        for r in reports:
            writer.writerow([extract(r) for extract in extractors])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    filename = _export_filename("reports", "csv")
    return StreamingResponse(
        _iter_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/pdf")
def export_reports_pdf(
    status: str | None = Query(default=None, description="Filter by status name"),
    category: str | None = Query(default=None, description="Filter by category name"),
    date_from: datetime | None = Query(default=None, description="Filter reports created on or after this datetime"),
    date_to: datetime | None = Query(default=None, description="Filter reports created on or before this datetime"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> StreamingResponse:
    """Render filtered reports as a PDF report. Officer/admin only. (FR-08)"""
    reports = report_service.export_reports(
        db, status=status, category=category, date_from=date_from, date_to=date_to,
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=12 * mm, rightMargin=12 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title="Reports export",
    )
    styles = getSampleStyleSheet()

    story = [
        Paragraph("Reports export", styles["Title"]),
        Paragraph(_pdf_filter_summary(status, category, date_from, date_to), styles["Normal"]),
        Spacer(1, 6 * mm),
    ]

    headers = [label for label, _ in _EXPORT_COLUMNS]
    extractors = [extractor for _, extractor in _EXPORT_COLUMNS]
    cell_style = styles["BodyText"]

    table_data = [headers]
    for r in reports:
        # Wrap each cell in Paragraph so long descriptions wrap inside the column.
        table_data.append([Paragraph(str(extract(r)), cell_style) for extract in extractors])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("GRID",       (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    story.append(table)

    if not reports:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("No reports matched the given filters.", styles["Italic"]))

    doc.build(story)
    buffer.seek(0)

    filename = _export_filename("reports", "pdf")
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _pdf_filter_summary(
    status: str | None,
    category: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> str:
    parts: list[str] = []
    if status:
        parts.append(f"status: {status}")
    if category:
        parts.append(f"category: {category}")
    if date_from:
        parts.append(f"from: {date_from.isoformat()}")
    if date_to:
        parts.append(f"to: {date_to.isoformat()}")
    if not parts:
        parts.append("no filters")
    parts.append(f"generated: {datetime.utcnow().isoformat(timespec='seconds')}Z")
    return " | ".join(parts)