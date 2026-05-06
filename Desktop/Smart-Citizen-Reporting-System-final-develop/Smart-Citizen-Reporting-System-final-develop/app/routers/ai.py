from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text, select
from sqlalchemy.orm import Session
import requests as _requests

from app.core.config import get_settings
from app.db.session import get_db
from app.models.category import Category
from app.services.ai_service import assign_priority, classify_text, generate_confirmation_mk
import os

router = APIRouter(prefix="/ai", tags=["ai"])


class AnalyzeReportRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=5000)
    category_id: int | None = None


class AnalyzeReportResponse(BaseModel):
    category_id: int | None = None
    priority: str | None = None
    ai_confirmation_text: str | None = None


def _normalize_key(value: str) -> str:
    return value.strip().casefold()


def _classifier_label_for_category(category_name: str) -> str:
    if category_name.strip().lower() == "safety":
        return "Safety (accidents and hazards)"
    return category_name


def _local_category_catalog() -> list[dict[str, object]]:
    return [
        {"id": 1, "name": "Infrastructure"},
        {"id": 2, "name": "Environment"},
        {"id": 3, "name": "Safety"},
        {"id": 4, "name": "Other"},
    ]


def _keyword_category_fallback(description: str) -> int | None:
    text = description.casefold()
    if any(keyword in text for keyword in [
        "fire", "smoke", "injur", "accident", "danger", "unsafe", "emergency", "explosion", "flood", "hazard",
        "пожар", "чад", "повред", "несреќ", "опас", "итно", "експлози", "поплав",
    ]):
        return 3
    if any(keyword in text for keyword in [
        "pothole", "road", "street", "light", "lamp", "sidewalk", "bridge", "broken", "hole", "infrastructure", "sewer", "pipe",
        "дупка", "пат", "улица", "светил", "тротоар", "мост", "скрш", "канализа", "цевк",
    ]):
        return 1
    if any(keyword in text for keyword in [
        "trash", "garbage", "waste", "litter", "pollution", "tree", "park", "smell", "environment", "dump",
        "ѓубре", "отпад", "загад", "дрво", "парк", "мирис", "депони",
    ]):
        return 2
    return None


@router.post("/analyze-report", response_model=AnalyzeReportResponse)
def analyze_report(
    payload: AnalyzeReportRequest,
    db: Session = Depends(get_db),
) -> AnalyzeReportResponse:
    """
    Analyze a report payload and return AI-generated fields.

    This endpoint does not insert/update rows directly. The caller is responsible
    for persisting returned values (for example, after inserting into Supabase).
    """
    settings = get_settings()

    category_id = payload.category_id

    # Try normal DB-backed path first; if the DB is unreachable, fall back to
    # fetching recent reports and categories from Supabase REST using the
    # configured anon key. This allows the AI endpoint to work even when the
    # local DB connection fails.
    categories_sorted: list[Category] = []
    recent_descriptions: list[str] = []

    try:
        categories = db.scalars(select(Category)).all()
        categories_sorted = sorted(categories, key=lambda c: c.name.casefold())

        if category_id is None and settings.ai_enabled and categories_sorted:
            candidate_labels = [_classifier_label_for_category(c.name) for c in categories_sorted]
            predicted_label = classify_text(
                payload.description,
                candidate_labels,
                min_confidence=settings.ai_min_confidence,
            )
            if predicted_label:
                predicted_key = _normalize_key(predicted_label)
                name_map = {_normalize_key(c.name): c.id for c in categories_sorted}
                classifier_map = {
                    _normalize_key(_classifier_label_for_category(c.name)): c.id for c in categories_sorted
                }
                category_id = name_map.get(predicted_key) or classifier_map.get(predicted_key)

            if category_id is None and settings.ai_default_category_name:
                fallback = next(
                    (
                        c.id
                        for c in categories_sorted
                        if c.name.casefold() == settings.ai_default_category_name.casefold()
                    ),
                    None,
                )
                category_id = fallback

        recent_rows = db.execute(
            text("SELECT description FROM reports ORDER BY created_at DESC LIMIT 20")
        ).all()
        recent_descriptions = [str(row[0]) for row in recent_rows if row and row[0]]
    except Exception:
        # DB access failed — try Supabase REST fallback.
        # Try environment variables as a last-resort (avoids requiring app restart
        # when .env was modified but get_settings() is cached by lru_cache).
        supabase_url = settings.supabase_url or os.getenv("SUPABASE_URL")
        supabase_anon = settings.supabase_anon_key or os.getenv("SUPABASE_ANON_KEY")

        # If still not configured, try to read a local .env file in the project root.
        if (not supabase_url or not supabase_anon) and os.path.exists(".env"):
            try:
                with open(".env", "r", encoding="utf-8") as f:
                    for ln in f:
                        if not supabase_url and ln.strip().upper().startswith("SUPABASE_URL="):
                            # simple parse: SUPABASE_URL="https://..." or SUPABASE_URL=https://...
                            val = ln.split("=", 1)[1].strip().strip('"')
                            supabase_url = supabase_url or val
                        if not supabase_anon and ln.strip().upper().startswith("SUPABASE_ANON_KEY="):
                            val = ln.split("=", 1)[1].strip().strip('"')
                            supabase_anon = supabase_anon or val
            except Exception:
                pass
        if not supabase_url or not supabase_anon:
            raise HTTPException(
                status_code=500,
                detail="AI analyze failed and no Supabase fallback is configured.",
            )

        base = supabase_url.rstrip("/")
        headers = {"apikey": supabase_anon, "Authorization": f"Bearer {supabase_anon}"}

        try:
            # Fetch categories
            resp = _requests.get(f"{base}/rest/v1/categories?select=id,name", headers=headers, timeout=10)
            resp.raise_for_status()
            cats = resp.json()
            categories_sorted = sorted(cats, key=lambda c: str(c.get("name", "")).casefold())

            if category_id is None and settings.ai_enabled and categories_sorted:
                candidate_labels = [_classifier_label_for_category(c.get("name", "")) for c in categories_sorted]
                predicted_label = classify_text(
                    payload.description,
                    candidate_labels,
                    min_confidence=settings.ai_min_confidence,
                )
                if predicted_label:
                    predicted_key = _normalize_key(predicted_label)
                    name_map = {_normalize_key(str(c.get("name", ""))): c.get("id") for c in categories_sorted}
                    classifier_map = {
                        _normalize_key(_classifier_label_for_category(str(c.get("name", "")))): c.get("id") for c in categories_sorted
                    }
                    category_id = name_map.get(predicted_key) or classifier_map.get(predicted_key)

                if category_id is None and settings.ai_default_category_name:
                    fallback = next(
                        (
                            c.get("id")
                            for c in categories_sorted
                            if str(c.get("name", "")).casefold() == settings.ai_default_category_name.casefold()
                        ),
                        None,
                    )
                    category_id = fallback

            # Fetch recent descriptions
            resp = _requests.get(f"{base}/rest/v1/reports?select=description&order=created_at.desc&limit=20", headers=headers, timeout=10)
            resp.raise_for_status()
            rows = resp.json()
            recent_descriptions = [str(r.get("description", "")) for r in rows if r.get("description")]
        except Exception:
            # Final local fallback: use the seeded category catalog and keyword matching.
            categories_sorted = _local_category_catalog()
            recent_descriptions = []

            if category_id is None and settings.ai_enabled:
                candidate_labels = [_classifier_label_for_category(str(c["name"])) for c in categories_sorted]
                predicted_label = classify_text(
                    payload.description,
                    candidate_labels,
                    min_confidence=settings.ai_min_confidence,
                )
                if predicted_label:
                    predicted_key = _normalize_key(predicted_label)
                    name_map = {_normalize_key(str(c["name"])): int(c["id"]) for c in categories_sorted}
                    classifier_map = {
                        _normalize_key(_classifier_label_for_category(str(c["name"]))): int(c["id"]) for c in categories_sorted
                    }
                    category_id = name_map.get(predicted_key) or classifier_map.get(predicted_key)

                if category_id is None and settings.ai_default_category_name:
                    fallback = next(
                        (
                            int(c["id"])
                            for c in categories_sorted
                            if str(c["name"]).casefold() == settings.ai_default_category_name.casefold()
                        ),
                        None,
                    )

                    # Prefer keyword fallback before defaulting to 'Other'.
                    category_id = _keyword_category_fallback(payload.description) or fallback

            if category_id is None:
                category_id = _keyword_category_fallback(payload.description)
            if category_id is None:
                category_id = 4

    priority = assign_priority(payload.description, recent_descriptions)

    category_name = None
    # categories_sorted may be list[Category] (DB) or list[dict] (Supabase fallback)
    if categories_sorted:
        first = categories_sorted[0]
        if isinstance(first, Category):
            category_name = next((c.name for c in categories_sorted if c.id == category_id), None)
        elif isinstance(first, dict):
            category_name = next((str(c.get("name")) for c in categories_sorted if c.get("id") == category_id), None)
        else:
            category_name = None

    ai_confirmation_text = generate_confirmation_mk(
        payload.description,
        category_label=category_name,
        priority=priority,
        possible_duplicate_of=None,
    )

    return AnalyzeReportResponse(
        category_id=category_id,
        priority=priority,
        ai_confirmation_text=ai_confirmation_text,
    )
