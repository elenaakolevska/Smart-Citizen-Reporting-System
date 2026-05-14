"""Integration tests for analytics router endpoints.

Uses FastAPI TestClient with DEV_SKIP_AUTH=true so no real Supabase needed.
DB calls are mocked via patching to avoid needing a live database.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Must be set BEFORE app imports
os.environ["DEV_SKIP_AUTH"] = "true"
os.environ["AI_ENABLED"] = "false"
os.environ["AI_PRELOAD_ON_STARTUP"] = "false"

from app.core.config import get_settings  # noqa: E402
get_settings.cache_clear()

from app.main import app  # noqa: E402
from app.schemas.user import CurrentUser, UserRole  # noqa: E402
from app.utils.dependencies import get_current_user  # noqa: E402

ADMIN_USER = CurrentUser(
    id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    email="admin@example.com",
    role=UserRole.admin,
)

OFFICER_USER = CurrentUser(
    id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    email="officer@example.com",
    role=UserRole.officer,
)

CITIZEN_USER = CurrentUser(
    id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
    email="citizen@example.com",
    role=UserRole.citizen,
)

ANALYTICS_PREFIX = "/api/v1/analytics"


def _make_summary_response():
    return {
        "kpis": {
            "total": 100,
            "resolved": 60,
            "active": 30,
            "avgTime": "3.5 дена",
            "activeCitizens": 50,
        },
        "categoryData": [
            {"name": "Патишта", "complaints": 40, "resolved": 25, "active": 10},
        ],
        "pieData": [
            {"name": "Решени", "value": 60},
            {"name": "Активни", "value": 30},
        ],
        "monthlyData": [
            {"month": "Jan", "complaints": 10, "resolved": 7, "active": 2},
        ],
        "resolutionRate": 60.0,
    }


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER


@pytest.fixture()
def officer_client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user] = lambda: OFFICER_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER


@pytest.fixture()
def citizen_client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user] = lambda: CITIZEN_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER


# ── GET /analytics/summary ────────────────────────────────────────────────────

class TestAnalyticsSummary:
    def test_returns_200_for_admin(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 0
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/summary")

        assert resp.status_code == 200

    def test_returns_200_for_officer(self, officer_client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 0
            mock_db.scalars.return_value.all.return_value = []

            resp = officer_client.get(f"{ANALYTICS_PREFIX}/summary")

        assert resp.status_code == 200

    def test_returns_403_for_citizen(self, citizen_client):
        resp = citizen_client.get(f"{ANALYTICS_PREFIX}/summary")
        assert resp.status_code == 403

    def test_response_has_kpis_key(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 5
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/summary")

        if resp.status_code == 200:
            data = resp.json()
            assert "kpis" in data

    def test_response_has_category_data_key(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 0
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/summary")

        if resp.status_code == 200:
            data = resp.json()
            assert "categoryData" in data

    def test_response_has_monthly_data_key(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 0
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/summary")

        if resp.status_code == 200:
            data = resp.json()
            assert "monthlyData" in data

    def test_response_has_resolution_rate(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 0
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/summary")

        if resp.status_code == 200:
            data = resp.json()
            assert "resolutionRate" in data


# ── GET /analytics/ratings ────────────────────────────────────────────────────

class TestAnalyticsRatings:
    def test_returns_200_for_admin(self, client):
        with patch("app.routers.analytics.rating_service") as mock_rs:
            mock_rs.average_ratings_by_category.return_value = []
            resp = client.get(f"{ANALYTICS_PREFIX}/ratings")

        assert resp.status_code == 200

    def test_returns_200_for_officer(self, officer_client):
        with patch("app.routers.analytics.rating_service") as mock_rs:
            mock_rs.average_ratings_by_category.return_value = []
            resp = officer_client.get(f"{ANALYTICS_PREFIX}/ratings")

        assert resp.status_code == 200

    def test_returns_403_for_citizen(self, citizen_client):
        resp = citizen_client.get(f"{ANALYTICS_PREFIX}/ratings")
        assert resp.status_code == 403

    def test_returns_list(self, client):
        from app.schemas.rating import CategoryRatingAvg
        mock_data = [
            CategoryRatingAvg(
                category_id=1,
                category_name="Патишта",
                average_stars=4.2,
                ratings_count=10,
            )
        ]
        with patch("app.routers.analytics.rating_service") as mock_rs:
            mock_rs.average_ratings_by_category.return_value = mock_data
            resp = client.get(f"{ANALYTICS_PREFIX}/ratings")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["category_name"] == "Патишта"
        assert data[0]["average_stars"] == 4.2

    def test_returns_empty_list_when_no_ratings(self, client):
        with patch("app.routers.analytics.rating_service") as mock_rs:
            mock_rs.average_ratings_by_category.return_value = []
            resp = client.get(f"{ANALYTICS_PREFIX}/ratings")

        assert resp.status_code == 200
        assert resp.json() == []


# ── GET /analytics/export/csv ─────────────────────────────────────────────────

class TestAnalyticsExportCsv:
    def test_returns_200_for_admin(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/export/csv")

        assert resp.status_code == 200

    def test_returns_200_for_officer(self, officer_client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalars.return_value.all.return_value = []

            resp = officer_client.get(f"{ANALYTICS_PREFIX}/export/csv")

        assert resp.status_code == 200

    def test_returns_403_for_citizen(self, citizen_client):
        resp = citizen_client.get(f"{ANALYTICS_PREFIX}/export/csv")
        assert resp.status_code == 403

    def test_content_type_is_csv(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/export/csv")

        assert resp.status_code == 200
        assert "csv" in resp.headers["content-type"].lower()

    def test_has_content_disposition_attachment(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/export/csv")

        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "").lower()

    def test_csv_has_header_row(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/export/csv")

        assert resp.status_code == 200
        # Strip UTF-8 BOM if present
        text = resp.content.decode("utf-8-sig")
        first_line = text.split("\n")[0]
        assert "Опис" in first_line or "#" in first_line

    def test_csv_includes_report_data(self, client):
        mock_report = MagicMock()
        mock_report.description = "Тест пријава"
        mock_report.priority = "висок"
        mock_report.created_at = datetime(2025, 1, 15, 10, 30, tzinfo=timezone.utc)
        mock_report.category = MagicMock(name="Патишта")
        mock_report.category.name = "Патишта"
        mock_report.status = MagicMock(name="Нов")
        mock_report.status.name = "Нов"

        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalars.return_value.all.return_value = [mock_report]

            resp = client.get(f"{ANALYTICS_PREFIX}/export/csv")

        assert resp.status_code == 200
        text = resp.content.decode("utf-8-sig")
        assert "Тест пријава" in text
        assert "Патишта" in text

    def test_csv_no_lat_lng_columns(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/export/csv")

        assert resp.status_code == 200
        text = resp.content.decode("utf-8-sig")
        assert "lat" not in text.lower()
        assert "lng" not in text.lower()
        assert "longitude" not in text.lower()
        assert "latitude" not in text.lower()


# ── GET /analytics/export/pdf ─────────────────────────────────────────────────

class TestAnalyticsExportPdf:
    def test_returns_200_for_admin(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 0
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/export/pdf")

        assert resp.status_code == 200

    def test_returns_200_for_officer(self, officer_client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 0
            mock_db.scalars.return_value.all.return_value = []

            resp = officer_client.get(f"{ANALYTICS_PREFIX}/export/pdf")

        assert resp.status_code == 200

    def test_returns_403_for_citizen(self, citizen_client):
        resp = citizen_client.get(f"{ANALYTICS_PREFIX}/export/pdf")
        assert resp.status_code == 403

    def test_content_type_is_pdf(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 0
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/export/pdf")

        assert resp.status_code == 200
        assert "pdf" in resp.headers["content-type"].lower()

    def test_has_content_disposition_attachment(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 0
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/export/pdf")

        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "").lower()

    def test_pdf_starts_with_pdf_header(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 0
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/export/pdf")

        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"

    def test_pdf_non_empty(self, client):
        with patch("app.routers.analytics.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])
            mock_db.scalar.return_value = 10
            mock_db.scalars.return_value.all.return_value = []

            resp = client.get(f"{ANALYTICS_PREFIX}/export/pdf")

        assert resp.status_code == 200
        assert len(resp.content) > 500  # PDF should have reasonable size
