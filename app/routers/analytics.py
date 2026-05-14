from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func
from datetime import datetime, timezone
from io import BytesIO
from app.db.session import get_db
from app.models.report import Report
from app.models.category import Category
from app.models.history import History
from app.models.status import Status
from app.models.user import User
from app.schemas.rating import CategoryRatingAvg
from app.schemas.user import CurrentUser, UserRole
from app.services import rating_service
from app.utils.dependencies import require_roles
from app.utils.pdf import register_cyrillic_font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import csv
import io


# Number of months included in monthly-trend KPIs (analytics summary + PDF).
MONTHLY_TREND_WINDOW = 6


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
        current_user: CurrentUser = Depends(require_roles(UserRole.admin, UserRole.officer)),
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
        current_user: CurrentUser = Depends(require_roles(UserRole.admin, UserRole.officer))
):
    resolved_status_ids = _status_ids_for_names(db, RESOLVED_STATUS_NAMES)
    active_status_ids = _status_ids_for_names(db, ACTIVE_STATUS_NAMES)

    # KPI Cards
    total_reports = _count_reports(db)
    resolved_reports = _count_reports(db, _status_filter(resolved_status_ids))
    active_reports = _count_reports(db, _status_filter(active_status_ids))
    active_citizens = db.scalar(select(func.count(User.id)).where(User.role == "citizen")) or 0

    # Average resolution time: earliest resolved history entry minus report creation time
    if resolved_status_ids:
        first_resolved = (
            select(History.report_id, func.min(History.created_at).label("resolved_at"))
            .where(History.status_id.in_(resolved_status_ids))
            .group_by(History.report_id)
            .subquery()
        )
        avg_seconds = db.scalar(
            select(func.avg(
                func.extract("epoch", first_resolved.c.resolved_at)
                - func.extract("epoch", Report.created_at)
            )).join(first_resolved, Report.id == first_resolved.c.report_id)
        )
        if avg_seconds and avg_seconds > 0:
            avg_resolution_time = f"{round(avg_seconds / 86400, 1)} дена"
        else:
            avg_resolution_time = "N/A"
    else:
        avg_resolution_time = "N/A"

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

    # LineChart: Monthly trend (last MONTHLY_TREND_WINDOW months, oldest → current)
    monthly_data = []
    current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for i in range(MONTHLY_TREND_WINDOW - 1, -1, -1):
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
        current_user: CurrentUser = Depends(require_roles(UserRole.admin, UserRole.officer))
):
    reports = db.scalars(
        select(Report).options(selectinload(Report.category), selectinload(Report.status))
    ).all()

    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=';')

    writer.writerow(["#", "Опис", "Категорија", "Статус", "Приоритет", "Датум на пријава"])

    for i, r in enumerate(reports, start=1):
        created = r.created_at.strftime("%d.%m.%Y %H:%M") if r.created_at else "-"
        writer.writerow([
            i,
            r.description,
            r.category.name if r.category else "-",
            r.status.name if r.status else "-",
            r.priority or "-",
            created,
        ])

    content = output.getvalue().encode("utf-8")
    filename = f"urbancare_prijavi_{datetime.now(timezone.utc).strftime('%d-%m-%Y')}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/pdf")
def export_pdf(
        db: Session = Depends(get_db),
        current_user: CurrentUser = Depends(require_roles(UserRole.admin, UserRole.officer))
):
    resolved_status_ids = _status_ids_for_names(db, RESOLVED_STATUS_NAMES)
    active_status_ids = _status_ids_for_names(db, ACTIVE_STATUS_NAMES)

    total = _count_reports(db)
    resolved = _count_reports(db, _status_filter(resolved_status_ids))
    active = _count_reports(db, _status_filter(active_status_ids))
    resolution_rate = round(resolved / total * 100, 1) if total > 0 else 0
    active_citizens = db.scalar(select(func.count(User.id)).where(User.role == "citizen")) or 0

    categories = db.scalars(select(Category)).all()
    category_rows = []
    for cat in categories:
        complaints = _count_reports(db, Report.category_id == cat.id)
        cat_resolved = _count_reports(db, Report.category_id == cat.id, _status_filter(resolved_status_ids))
        cat_active = _count_reports(db, Report.category_id == cat.id, _status_filter(active_status_ids))
        category_rows.append([cat.name, str(complaints), str(cat_resolved), str(cat_active)])

    current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_rows = []
    for i in range(MONTHLY_TREND_WINDOW - 1, -1, -1):
        month_start = _add_months(current_month, -i)
        month_end = _add_months(month_start, 1)
        count = _count_reports(db, Report.created_at >= month_start, Report.created_at < month_end)
        m_resolved = _count_reports(db, _status_filter(resolved_status_ids), Report.created_at >= month_start,
                                    Report.created_at < month_end)
        m_active = _count_reports(db, _status_filter(active_status_ids), Report.created_at >= month_start,
                                  Report.created_at < month_end)
        monthly_rows.append([month_start.strftime("%b %Y"), str(count), str(m_resolved), str(m_active)])

    font_regular, font_bold = register_cyrillic_font()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="Analytics Report",
    )
    title_style = ParagraphStyle("CyrTitle", fontName=font_bold, fontSize=18, spaceAfter=4)
    normal_style = ParagraphStyle("CyrNormal", fontName=font_regular, fontSize=10, spaceAfter=2)
    heading_style = ParagraphStyle("CyrHeading", fontName=font_bold, fontSize=12, spaceAfter=4, spaceBefore=6)

    header_color = colors.HexColor("#1f4e79")
    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), font_bold),
        ("FONTNAME", (0, 1), (-1, -1), font_regular),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWHEIGHT", (0, 0), (-1, -1), 16),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ])

    available_width = A4[0] - 36 * mm

    kpi_data = [
        ["Вкупно пријави", "Решени", "Активни", "Стапка на решавање", "Активни граѓани"],
        [str(total), str(resolved), str(active), f"{resolution_rate}%", str(active_citizens)],
    ]
    kpi_table = Table(kpi_data, colWidths=[available_width / 5] * 5)
    kpi_table.setStyle(table_style)

    cat_header = [["Категорија", "Вкупно", "Решени", "Активни"]]
    cat_widths = [available_width * 0.55, available_width * 0.15, available_width * 0.15, available_width * 0.15]
    cat_table = Table(cat_header + category_rows, colWidths=cat_widths)
    cat_table.setStyle(table_style)

    month_header = [["Месец", "Вкупно", "Решени", "Активни"]]
    month_widths = [available_width * 0.40, available_width * 0.20, available_width * 0.20, available_width * 0.20]
    month_table = Table(month_header + monthly_rows, colWidths=month_widths)
    month_table.setStyle(table_style)

    story = [
        Paragraph("Аналитички извештај", title_style),
        Paragraph(f"Генерирано: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}", normal_style),
        Spacer(1, 6 * mm),
        Paragraph("Клучни показатели", heading_style),
        Spacer(1, 2 * mm),
        kpi_table,
        Spacer(1, 6 * mm),
        Paragraph("Пријави по категорија", heading_style),
        Spacer(1, 2 * mm),
        cat_table,
        Spacer(1, 6 * mm),
        Paragraph("Месечен тренд (последни 6 месеци)", heading_style),
        Spacer(1, 2 * mm),
        month_table,
    ]

    doc.build(story)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=analytics_export.pdf"}
    )
