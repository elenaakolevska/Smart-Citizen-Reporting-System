from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import Report

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────
TEXT_SIMILARITY_THRESHOLD = 75   # rapidfuzz score 0-100
MAX_DISTANCE_METERS       = 100  # geographic radius
TIME_WINDOW_HOURS         = 24   # how far back to look


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance between two lat/lon points in metres."""
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def check_duplicate(
    description: str,
    latitude: float | None,
    longitude: float | None,
    created_at: datetime,
    db: Session,
    exclude_id: UUID | None = None,
) -> UUID | None:
    """
    Compare the incoming report against recent reports in the DB.

    Returns the `id` of the most similar existing report if ALL three
    conditions are met, otherwise returns None.

    Conditions (ALL must pass):
        1. Text similarity  >= TEXT_SIMILARITY_THRESHOLD  (rapidfuzz token_set_ratio)
        2. Distance         <= MAX_DISTANCE_METERS        (haversine, skipped if no coords)
        3. Time difference  <= TIME_WINDOW_HOURS
    """
    window_start = created_at - timedelta(hours=TIME_WINDOW_HOURS)
    window_end   = created_at + timedelta(hours=TIME_WINDOW_HOURS)

    # Fetch only candidate reports within the time window — avoids full table scan
    stmt = (
        select(Report)
        .where(Report.created_at >= window_start)
        .where(Report.created_at <= window_end)
    )
    if exclude_id is not None:
        stmt = stmt.where(Report.id != exclude_id)

    candidates = db.scalars(stmt).all()

    best_id: UUID | None = None
    best_score: float = -1.0

    for candidate in candidates:
        # ── 1. Text similarity ────────────────────────────────────────────────
        text_score = fuzz.token_set_ratio(description, candidate.description)
        if text_score < TEXT_SIMILARITY_THRESHOLD:
            continue

        # ── 2. Location proximity ─────────────────────────────────────────────
        if latitude is not None and longitude is not None:
            if candidate.latitude is None or candidate.longitude is None:
                # candidate has no coords — skip location check, still consider it
                pass
            else:
                distance = _haversine_meters(latitude, longitude, candidate.latitude, candidate.longitude)
                if distance > MAX_DISTANCE_METERS:
                    continue

        # ── 3. Time window (already filtered at query level, kept for clarity) ─
        diff = abs((created_at - candidate.created_at).total_seconds())
        if diff > TIME_WINDOW_HOURS * 3600:
            continue

        # ── All checks passed — track highest text score ───────────────────────
        if text_score > best_score:
            best_score = text_score
            best_id = candidate.id
            logger.info(
                "Possible duplicate detected: incoming report matches report id=%s "
                "(text_score=%.1f, distance check passed, within time window)",
                candidate.id,
                text_score,
            )

    return best_id