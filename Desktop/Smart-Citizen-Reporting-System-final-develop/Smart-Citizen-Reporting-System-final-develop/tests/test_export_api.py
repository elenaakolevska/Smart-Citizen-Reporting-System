"""E2E tests for the FR-08 export endpoints.

  GET /reports/export/csv  — officer/admin
  GET /reports/export/pdf  — officer/admin

Requires a live database with seeded users + statuses + categories.

Run:
    python -m pytest tests/test_export_api.py -v
"""

from __future__ import annotations

import csv
import io
import os
import re
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

# ── Must set BEFORE importing app ────────────────────────────────────────────
os.environ["DEV_SKIP_AUTH"] = "true"
os.environ["AI_ENABLED"] = "false"
os.environ["AI_PRELOAD_ON_STARTUP"] = "false"

from app.core.config import get_settings  # noqa: E402
get_settings.cache_clear()

from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.report import Report  # noqa: E402
from app.schemas.user import CurrentUser, UserRole  # noqa: E402
from app.utils.dependencies import get_current_user  # noqa: E402


REPORTS_PREFIX = "/api/v1/reports"
EXPORT_DESC_PREFIX = "E2E-EXPORT:"

CITIZEN_USER = CurrentUser(
    id=uuid.UUID("12345678-1234-1234-1234-123456789012"),
    email="citizen@example.com",
    role=UserRole.citizen,
)
OFFICER_USER = CurrentUser(
    id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    email="officer@example.com",
    role=UserRole.officer,
)
ADMIN_USER = CurrentUser(
    id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    email="admin@example.com",
    role=UserRole.admin,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def cleanup_test_reports():
    yield
    db: Session = SessionLocal()
    try:
        db.query(Report).filter(Report.description.like(f"{EXPORT_DESC_PREFIX}%")).delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


def _act_as(user: CurrentUser):
    app.dependency_overrides[get_current_user] = lambda: user


def _seed_report(client: TestClient, suffix: str) -> str:
    """Create a report owned by ADMIN. Returns the new UUID id as a string."""
    _act_as(ADMIN_USER)
    resp = client.post(REPORTS_PREFIX, json={"description": f"{EXPORT_DESC_PREFIX} {suffix}"})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

class TestExportCSV:
    def test_admin_returns_200_with_csv_headers(self, client: TestClient):
        _seed_report(client, "csv-row-1")

        _act_as(ADMIN_USER)
        resp = client.get(f"{REPORTS_PREFIX}/export/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "charset=utf-8" in resp.headers["content-type"]

        cd = resp.headers["content-disposition"]
        assert cd.startswith("attachment; filename=")
        assert re.search(r'filename="reports-\d{8}-\d{6}\.csv"', cd)

    def test_officer_can_export(self, client: TestClient):
        _act_as(OFFICER_USER)
        resp = client.get(f"{REPORTS_PREFIX}/export/csv")
        assert resp.status_code == 200

    def test_citizen_forbidden(self, client: TestClient):
        _act_as(CITIZEN_USER)
        resp = client.get(f"{REPORTS_PREFIX}/export/csv")
        assert resp.status_code == 403

    def test_csv_body_has_header_row_and_seeded_data(self, client: TestClient):
        rid = _seed_report(client, "csv-content-check")

        _act_as(ADMIN_USER)
        resp = client.get(f"{REPORTS_PREFIX}/export/csv")
        assert resp.status_code == 200

        # Strip the leading UTF-8 BOM the endpoint emits for Excel compatibility.
        body = resp.text.lstrip("﻿")
        rows = list(csv.reader(io.StringIO(body)))

        assert len(rows) >= 2  # header + ≥1 row
        header = rows[0]
        # Report.title was removed in the supabase-integration merge, so the
        # CSV no longer carries a Title column.
        for col in ["ID", "Description", "Category", "Status", "Created at"]:
            assert col in header

        ids = [r[header.index("ID")] for r in rows[1:]]
        assert rid in ids  # rid is already a UUID string

    def test_unknown_status_filter_returns_empty_body(self, client: TestClient):
        _seed_report(client, "csv-unknown-status")

        _act_as(ADMIN_USER)
        resp = client.get(
            f"{REPORTS_PREFIX}/export/csv",
            params={"status": "DOES-NOT-EXIST-ANYWHERE"},
        )
        assert resp.status_code == 200
        body = resp.text.lstrip("﻿")
        rows = list(csv.reader(io.StringIO(body)))
        # Header only, no data rows — typo'd filter doesn't silently widen results
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

class TestExportPDF:
    def test_admin_returns_valid_pdf(self, client: TestClient):
        _seed_report(client, "pdf-row-1")

        _act_as(ADMIN_USER)
        resp = client.get(f"{REPORTS_PREFIX}/export/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF-")
        # PDF should also have an EOF marker — proves the doc was finalized
        assert b"%%EOF" in resp.content[-1024:]

    def test_pdf_content_disposition_is_attachment(self, client: TestClient):
        _act_as(ADMIN_USER)
        resp = client.get(f"{REPORTS_PREFIX}/export/pdf")
        assert resp.status_code == 200
        cd = resp.headers["content-disposition"]
        assert cd.startswith("attachment; filename=")
        assert re.search(r'filename="reports-\d{8}-\d{6}\.pdf"', cd)

    def test_officer_can_export_pdf(self, client: TestClient):
        _act_as(OFFICER_USER)
        resp = client.get(f"{REPORTS_PREFIX}/export/pdf")
        assert resp.status_code == 200

    def test_citizen_forbidden(self, client: TestClient):
        _act_as(CITIZEN_USER)
        resp = client.get(f"{REPORTS_PREFIX}/export/pdf")
        assert resp.status_code == 403

    def test_pdf_renders_when_no_results(self, client: TestClient):
        """With a filter that matches nothing, the endpoint still returns a valid PDF."""
        _act_as(ADMIN_USER)
        resp = client.get(
            f"{REPORTS_PREFIX}/export/pdf",
            params={"status": "DOES-NOT-EXIST-ANYWHERE"},
        )
        assert resp.status_code == 200
        assert resp.content.startswith(b"%PDF-")
