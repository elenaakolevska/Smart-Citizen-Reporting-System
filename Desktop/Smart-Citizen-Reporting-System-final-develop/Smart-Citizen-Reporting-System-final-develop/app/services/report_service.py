from __future__ import annotations

import logging
from time import perf_counter
from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.attachment import Attachment
from app.models.category import Category
from app.models.comment import Comment
from app.models.history import History
from app.models.report import Report
from app.models.status import Status
from app.schemas.attachment import AttachmentRead
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
from app.services.ai_service import assign_priority, classify_text, generate_confirmation_message, generate_confirmation_mk
from app.utils.duplicate_detection import check_duplicate

logger = logging.getLogger(__name__)

DEFAULT_SUBMITTED_STATUS = "Submitted"


def _normalize_category_key(value: str) -> str:
    return value.strip().casefold()


def _classifier_label_for_category(category_name: str) -> str:
    if category_name.strip().lower() == "safety":
        return "Safety (accidents and hazards)"
    return category_name


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def create_report(db: Session, *, report_in: ReportCreate, current_user: CurrentUser) -> ReportRead:
    now = datetime.now(tz=timezone.utc)

    default_status_id = db.scalar(
        select(Status.id).where(func.lower(Status.name) == DEFAULT_SUBMITTED_STATUS.lower())
    )

    category_id = report_in.category_id
    if category_id is not None:
        if category_id <= 0:
            logger.info("Ignoring invalid category_id=%r on report creation.", category_id)
            category_id = None
        elif db.get(Category, category_id) is None:
            logger.info("Ignoring unknown category_id=%r on report creation.", category_id)
            category_id = None

    possible_duplicate_of = check_duplicate(
        description=report_in.description,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        created_at=now,
        db=db,
    )

    if possible_duplicate_of is not None:
        logger.warning(
            "New report may be a duplicate of report id=%s — saving with flag set.",
            possible_duplicate_of,
        )

    report = Report(
        description=report_in.description,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        user_id=current_user.id,
        category_id=category_id,
        status_id=default_status_id,
        possible_duplicate_of=possible_duplicate_of,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _to_report_read(report)


def _to_report_read(report: Report) -> ReportRead:
    return ReportRead(
        id=report.id,
        description=report.description,
        latitude=report.latitude,
        longitude=report.longitude,
        priority=report.priority,
        category_id=report.category_id,
        status_id=report.status_id,
        user_id=report.user_id,
        created_at=report.created_at,
        updated_at=report.updated_at,
        possible_duplicate_of=report.possible_duplicate_of,
        ai_confirmation_text=report.ai_confirmation_text,
    )


def run_report_ai_pipeline(report_id: UUID) -> None:
    """
    Background AI pipeline for a report:
    - classify description -> set category_id (if still NULL)
    - generate a confirmation message (optional persisted comment)
    - generate Macedonian AI confirmation (FR-03)

    This must never raise: report creation should not fail due to AI.
    """
    settings = get_settings()
    if not settings.ai_enabled:
        return

    total_start = perf_counter()
    db: Session = SessionLocal()
    try:
        report = db.get(Report, report_id)
        if report is None:
            logger.warning("AI pipeline: report_id=%s not found — skipping.", report_id)
            return

        categories = db.scalars(select(Category)).all()
        if not categories:
            logger.warning("AI pipeline: no categories found — skipping for report_id=%s.", report_id)
            categories_sorted: list[Category] = []
        else:
            categories_sorted = sorted(categories, key=lambda c: c.name.casefold())

        category_name_key_to_id = {_normalize_category_key(c.name): c.id for c in categories_sorted}
        classifier_label_key_to_id = {
            _normalize_category_key(_classifier_label_for_category(c.name)): c.id for c in categories_sorted
        }
        candidate_labels = [_classifier_label_for_category(c.name) for c in categories_sorted]

        predicted_label: str | None = None
        category_changed = False

        # Only auto-assign when the report still has no category.
        if report.category_id is None and candidate_labels:
            try:
                predicted_label = classify_text(
                    report.description,
                    candidate_labels,
                    min_confidence=settings.ai_min_confidence,
                )
            except Exception:
                logger.warning("AI unavailable — skipping for report_id=%s.", report_id, exc_info=True)
                predicted_label = None

        if report.category_id is None and predicted_label:
            predicted_key = _normalize_category_key(predicted_label)
            new_category_id = (
                category_name_key_to_id.get(predicted_key)
                or classifier_label_key_to_id.get(predicted_key)
            )
            if new_category_id is not None:
                report.category_id = new_category_id
                category_changed = True
                logger.info(
                    "Auto-assigned category_id=%d ('%s') for report_id=%s",
                    new_category_id, predicted_label, report_id,
                )
            else:
                logger.warning("AI label not matched to DB category: %s", predicted_label)

        if report.category_id is None and settings.ai_default_category_name:
            fallback_id = category_name_key_to_id.get(
                _normalize_category_key(settings.ai_default_category_name)
            )
            if fallback_id is not None:
                report.category_id = fallback_id
                category_changed = True
                logger.info(
                    "Applied fallback category_id=%d ('%s') for report_id=%s",
                    fallback_id, settings.ai_default_category_name, report_id,
                )
            else:
                logger.warning(
                    "Fallback category '%s' not found in DB — left NULL for report_id=%s.",
                    settings.ai_default_category_name, report_id,
                )

        if category_changed:
            db.commit()

        if not (report.priority or "").strip():
            try:
                recent_descriptions = db.scalars(
                    select(Report.description)
                    .where(Report.id != report.id)
                    .order_by(Report.created_at.desc())
                    .limit(20)
                ).all()
                report.priority = assign_priority(report.description, list(recent_descriptions))
                db.commit()
                logger.info("Auto-assigned priority='%s' for report_id=%s", report.priority, report_id)
            except Exception:
                db.rollback()
                logger.warning(
                    "Priority assignment failed for report_id=%s — continuing pipeline.",
                    report_id,
                    exc_info=True,
                )

        # Resolve category name for messages (after classification is settled)
        category_label_for_message: str | None = None
        if report.category_id is not None:
            category_label_for_message = next(
                (c.name for c in categories_sorted if c.id == report.category_id), None
            )

        # --- English confirmation (existing) ---
        message = generate_confirmation_message(
            report.description,
            category_label=category_label_for_message,
            possible_duplicate_of=report.possible_duplicate_of,
        )

        # AI-generated Macedonian confirmation (with priority)

        try:
            mk_text = generate_confirmation_mk(
                report.description,
                category_label=category_label_for_message,
                priority=report.priority,                      # ← CR-02
                possible_duplicate_of=report.possible_duplicate_of,
            )
            report.ai_confirmation_text = mk_text
            db.commit()
            logger.info("ai_confirmation_text saved for report_id=%s", report_id)
        except Exception:
            logger.warning(
                "Unexpected error saving ai_confirmation_text for report_id=%s — skipping.",
                report_id,
                exc_info=True,
            )
        # ------------------------------------------------------------------ #

        # --- Persist EN confirmation as a comment (optional) ---
        if message and settings.ai_confirmation_comment_user_id is not None:
            existing = db.scalars(
                select(Comment)
                .where(Comment.report_id == report.id)
                .where(Comment.user_id == settings.ai_confirmation_comment_user_id)
            ).first()
            if existing is None:
                db.add(Comment(
                    report_id=report.id,
                    user_id=settings.ai_confirmation_comment_user_id,
                    content=message,
                ))
                try:
                    db.commit()
                except Exception:
                    db.rollback()
                    logger.warning(
                        "AI confirmation persistence failed for report_id=%s.", report_id, exc_info=True
                    )

        elapsed_ms = (perf_counter() - total_start) * 1000
        logger.info("AI pipeline latency: %.0fms", elapsed_ms)
    except Exception:
        logger.warning("AI pipeline failed for report_id=%s — skipping.", report_id, exc_info=True)
    finally:
        db.close()

def list_reports(db: Session, *, current_user: CurrentUser) -> list[ReportRead]:
    try:
        stmt = select(Report)
        if current_user.role == UserRole.citizen:
            stmt = stmt.where(Report.user_id == current_user.id)
        return [_to_report_read(r) for r in db.scalars(stmt).all()]
    except Exception as exc:
        logger.warning(
            "list_reports failed for user_id=%s role=%s; returning empty list: %s",
            current_user.id,
            current_user.role,
            exc,
        )
        return []


def _get_or_404(db: Session, report_id: UUID) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def _record_status_history(
    db: Session,
    report: Report,
    new_status_id: int | None,
    changed_by_user_id: UUID,
) -> None:
    db.add(History(
        report_id=report.id,
        old_status_id=report.status_id,
        status_id=new_status_id,
        changed_by_user_id=changed_by_user_id,
    ))


def get_report(db: Session, *, report_id: UUID, current_user: CurrentUser) -> ReportRead:
    report = _get_or_404(db, report_id)
    if current_user.role == UserRole.citizen and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return _to_report_read(report)


def update_report(
    db: Session, *, report_id: UUID, report_in: ReportUpdate, current_user: CurrentUser
) -> ReportRead:
    report = _get_or_404(db, report_id)
    if current_user.role == UserRole.citizen and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    update_data = report_in.model_dump(exclude_unset=True)

    if current_user.role == UserRole.citizen:
        update_data.pop("category_id", None)
        update_data.pop("status_id", None)

    new_status_id = update_data.get("status_id", report.status_id)
    if new_status_id != report.status_id:
        _record_status_history(db, report, new_status_id, current_user.id)

    for field, value in update_data.items():
        setattr(report, field, value)

    db.commit()
    db.refresh(report)
    return _to_report_read(report)


def update_status(
    db: Session, *, report_id: UUID, status_in: StatusUpdate, current_user: CurrentUser
) -> ReportRead:
    report = _get_or_404(db, report_id)
    status_changed = status_in.status_id != report.status_id
    if status_changed:
        _record_status_history(db, report, status_in.status_id, current_user.id)
    report.status_id = status_in.status_id

    # CR-06: when a report is closed, invite the citizen to rate it.
    if status_changed:
        new_status = db.get(Status, status_in.status_id)
        if new_status is not None and new_status.name == "Closed":
            from app.services.notification_service import create_rating_invitation_notification
            create_rating_invitation_notification(db, report=report)

    db.commit()
    db.refresh(report)
    return _to_report_read(report)


def update_priority(
    db: Session,
    *,
    report_id: UUID,
    priority_in: PriorityUpdate,
    current_user: CurrentUser,
) -> ReportRead:
    report = _get_or_404(db, report_id)
    report.priority = priority_in.priority
    db.commit()
    db.refresh(report)
    return _to_report_read(report)


def delete_report(db: Session, *, report_id: UUID, current_user: CurrentUser) -> None:
    report = _get_or_404(db, report_id)
    is_owner = report.user_id == current_user.id
    allowed = current_user.role == UserRole.admin or (
        current_user.role == UserRole.citizen and is_owner
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(report)
    db.commit()


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

def list_comments(
    db: Session, *, report_id: UUID, current_user: CurrentUser
) -> list[CommentRead]:
    report = _get_or_404(db, report_id)
    if current_user.role == UserRole.citizen and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    comments = db.scalars(
        select(Comment)
        .where(Comment.report_id == report_id)
        .order_by(Comment.created_at.asc())
    ).all()
    return [CommentRead.model_validate(c) for c in comments]


def create_comment(
    db: Session, *, report_id: UUID, comment_in: CommentCreate, current_user: CurrentUser
) -> CommentRead:
    if current_user.role not in [UserRole.officer, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Only officers and admins can comment")

    report = _get_or_404(db, report_id)

    comment = Comment(
        report_id=report.id,
        user_id=current_user.id,
        content=comment_in.content,
    )
    db.add(comment)

    from app.services.notification_service import create_comment_notification
    create_comment_notification(db, report=report, commenter_user_id=current_user.id)

    db.commit()
    db.refresh(comment)
    return CommentRead.model_validate(comment)


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

def list_attachments(
    db: Session, *, report_id: UUID, current_user: CurrentUser
) -> list[AttachmentRead]:
    report = _get_or_404(db, report_id)
    if current_user.role == UserRole.citizen and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    attachments = db.scalars(
        select(Attachment)
        .where(Attachment.report_id == report_id)
        .order_by(Attachment.created_at.asc())
    ).all()
    return [AttachmentRead.model_validate(a) for a in attachments]


def create_attachment(
    db: Session,
    *,
    report_id: UUID,
    file_url: str,
    original_filename: str,
    content_type: str,
    file_size_bytes: int,
    current_user: CurrentUser,
) -> AttachmentRead:
    if current_user.role not in [UserRole.officer, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Only officers and admins can upload attachments")

    report = _get_or_404(db, report_id)

    attachment = Attachment(
        report_id=report.id,
        file_url=file_url,
        original_filename=original_filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return AttachmentRead.model_validate(attachment)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_reports(
    db: Session,
    *,
    status: str | None = None,
    category: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[Report]:
    """Return reports filtered for export, with category/status eagerly loaded.

    Filters are applied conjunctively. An unknown status/category name yields
    no matches (rather than being silently dropped) so the caller never gets
    back a wider set than they asked for.
    """
    stmt = (
        select(Report)
        .options(joinedload(Report.category), joinedload(Report.status))
        .order_by(Report.created_at.desc())
    )

    if status is not None:
        status_row = db.scalars(select(Status).where(Status.name == status)).first()
        if status_row is None:
            return []
        stmt = stmt.where(Report.status_id == status_row.id)

    if category is not None:
        category_row = db.scalars(select(Category).where(Category.name == category)).first()
        if category_row is None:
            return []
        stmt = stmt.where(Report.category_id == category_row.id)

    if date_from is not None:
        stmt = stmt.where(Report.created_at >= date_from)

    if date_to is not None:
        stmt = stmt.where(Report.created_at <= date_to)

    return list(db.scalars(stmt).unique().all())