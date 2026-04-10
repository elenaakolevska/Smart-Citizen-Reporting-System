from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.report import Report
from app.schemas.report import ReportCreate, ReportRead
from app.schemas.user import CurrentUser
from app.services.ai_service import classify_text


def create_report(db: Session, *, report_in: ReportCreate, current_user: CurrentUser) -> ReportRead:
    # AI classification (optional)
    category_name = classify_text(report_in.description)

    # TODO: ако имаш Category табела → најди ID според category_name
    category_id = report_in.category_id

    new_report = Report(
        description=report_in.description,
        category_id=category_id,
        status_id=1,  # default (пример: Pending)
        user_id=current_user.id,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        created_at=datetime.now(timezone.utc),
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return ReportRead.model_validate(new_report)


def list_reports(
    db: Session,
    *,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 10,
    status_id: int | None = None,
    category_id: int | None = None,
) -> list[ReportRead]:

    query = db.query(Report)

    # RBAC
    if current_user.role == "citizen":
        query = query.filter(Report.user_id == current_user.id)

    # filters
    if status_id:
        query = query.filter(Report.status_id == status_id)

    if category_id:
        query = query.filter(Report.category_id == category_id)

    # pagination
    reports = query.offset((page - 1) * page_size).limit(page_size).all()

    return [ReportRead.model_validate(r) for r in reports]


def get_report(
    db: Session,
    *,
    report_id: int,
    current_user: CurrentUser,
) -> ReportRead:

    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise Exception("Report not found")

    # RBAC check
    if current_user.role == "citizen" and report.user_id != current_user.id:
        raise Exception("Unauthorized")

    return ReportRead.model_validate(report)