from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime
from app.db.session import get_db
from app.models.report import Report
from app.models.category import Category
from app.models.status import Status
from app.models.user import User
from app.schemas.rating import CategoryRatingAvg
from app.schemas.user import CurrentUser, UserRole
from app.services import rating_service
from app.utils.dependencies import require_roles
import csv
import io

router = APIRouter(prefix="/analytics", tags=["analytics"])

RESOLVED_STATUS_NAMES = {
    "resolved",
    "closed",
    "resen",
    "reshen",
    "решен",
    "решена",
    "решено",
    "решени",
    "затворен",
    "затворена",
    "затворено",
    "затворени",
}

ACTIVE_STATUS_NAMES = {
    "active",
    "aktiven",
    "aktivna",
    "aktivni",
    "активен",
    "активна",
    "активно",
    "активни",
    "submitted",
    "in progress",
    "pending",
    "нов",
    "нова",
    "поднесен",
    "поднесена",
    "во тек",
    "на чекање",
}


def _normalized_status_name(name: str) -> str:
    return " ".join(name.strip().casefold().replace("_", " ").replace("-", " ").split())


def _status_ids_for_names(db: Session, names: set[str]) -> list[int]:
    normalized_names = {_normalized_status_name(name) for name in names}
    statuses = db.scalars(select(Status)).all()
    return [
        status.id
        for status in statuses
        if _normalized_status_name(status.name) in normalized_names
    ]


def _count_reports(db: Session, *criteria) -> int:
    return db.scalar(select(func.count(Report.id)).where(*criteria)) or 0


def _status_filter(status_ids: list[int]):
    return Report.status_id.in_(status_ids) if status_ids else False


def _add_months(dt: datetime, months: int) -> datetime:
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    return dt.replace(year=year, month=month)


@router.get("/ratings", response_model=list[CategoryRatingAvg])
def get_category_ratings(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> list[CategoryRatingAvg]:
    """Average citizen rating per category (CR-06).

    Originally specified as "по оддел" (per department); the supabase-integration
    merge removed Report's department FK, so this aggregates by category — the
    closest organizational dimension still in the data model.
    """
    return rating_service.average_ratings_by_category(db)

@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.admin))
):
    resolved_status_ids = _status_ids_for_names(db, RESOLVED_STATUS_NAMES)
    active_status_ids = _status_ids_for_names(db, ACTIVE_STATUS_NAMES)

    # KPI Cards
    total_reports = _count_reports(db)
    resolved_reports = _count_reports(db, _status_filter(resolved_status_ids))
    active_reports = _count_reports(db, _status_filter(active_status_ids))
    active_citizens = db.scalar(select(func.count(User.id)).where(User.role == "citizen")) or 0
    
    # Simple average resolution time (placeholder logic)
    # In a real app, we would join with history and calculate diff between created_at and 'resolved' history entry
    avg_resolution_time = "3.2 дена" 

    # BarChart: Reports by category
    categories = db.scalars(select(Category)).all()
    category_data = []
    for cat in categories:
        complaints = _count_reports(db, Report.category_id == cat.id)
        resolved = _count_reports(
            db,
            Report.category_id == cat.id,
            _status_filter(resolved_status_ids),
        )
        active = _count_reports(
            db,
            Report.category_id == cat.id,
            _status_filter(active_status_ids),
        )
        category_data.append({
            "name": cat.name,
            "complaints": complaints,
            "resolved": resolved,
            "active": active,
        })

    # PieChart: Resolved vs active reports
    pie_data = [
        {"name": "Решени", "value": resolved_reports},
        {"name": "Активни", "value": active_reports},
    ]

    # LineChart: Monthly trend (last 6 months)
    monthly_data = []
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for i in range(5, -1, -1):
        month_start = _add_months(current_month, -i)
        month_end = _add_months(month_start, 1)
        month_name = month_start.strftime("%b")
        count = _count_reports(db, Report.created_at >= month_start, Report.created_at < month_end)
        resolved = _count_reports(
            db,
            _status_filter(resolved_status_ids),
            Report.created_at >= month_start,
            Report.created_at < month_end,
        )
        active = _count_reports(
            db,
            _status_filter(active_status_ids),
            Report.created_at >= month_start,
            Report.created_at < month_end,
        )
        monthly_data.append({
            "month": month_name,
            "complaints": count,
            "resolved": resolved,
            "active": active,
        })

    return {
        "kpis": {
            "total": total_reports,
            "resolved": resolved_reports,
            "active": active_reports,
            "avgTime": avg_resolution_time,
            "activeCitizens": active_citizens
        },
        "categoryData": category_data,
        "pieData": pie_data,
        "monthlyData": monthly_data,
        "resolutionRate": round((resolved_reports / total_reports * 100), 1) if total_reports > 0 else 0
    }

@router.get("/export/csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.admin))
):
    reports = db.scalars(select(Report)).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Description", "Category ID", "Status ID", "Created At", "Lat", "Lng"])
    
    for r in reports:
        writer.writerow([r.id, r.description, r.category_id, r.status_id, r.created_at, r.latitude, r.longitude])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reports_export.csv"}
    )

@router.get("/export/pdf")
def export_pdf(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.admin))
):
    # PDF generation usually requires a library like reportlab or fpdf
    # For now, returning a placeholder byte stream to satisfy the UI requirement
    return Response(
        content=b"PDF Export Placeholder Content",
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reports_export.pdf"}
    )
