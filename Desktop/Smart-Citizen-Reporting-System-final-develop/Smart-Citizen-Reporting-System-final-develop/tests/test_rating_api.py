"""E2E tests for the rating + analytics-ratings + close-notification flow (CR-06).

Requires a live database with the seed applied (users + statuses table populated;
specifically, a status row named "Closed" must exist).

Run:
    python -m pytest tests/test_rating_api.py -v
"""

from __future__ import annotations

import os
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
from app.models.notification import Notification  # noqa: E402
from app.models.rating import Rating  # noqa: E402
from app.models.report import Report  # noqa: E402
from app.models.status import Status  # noqa: E402
from app.schemas.user import CurrentUser, UserRole  # noqa: E402
from app.utils.dependencies import DEV_USER, get_current_user  # noqa: E402


REPORTS_PREFIX = "/api/v1/reports"
ANALYTICS_PREFIX = "/api/v1/analytics"

# These UUIDs must exist in the seeded `users` table.
CITIZEN_USER_ID = uuid.UUID("12345678-1234-1234-1234-123456789012")  # same as DEV_USER, but role=citizen
OFFICER_USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ADMIN_USER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

CITIZEN_USER = CurrentUser(id=CITIZEN_USER_ID, email="citizen@example.com", role=UserRole.citizen)
OFFICER_USER = CurrentUser(id=OFFICER_USER_ID, email="officer@example.com", role=UserRole.officer)
ADMIN_USER = CurrentUser(id=ADMIN_USER_ID, email="admin@example.com", role=UserRole.admin)

# A second citizen for "different owner" tests
OTHER_CITIZEN_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
OTHER_CITIZEN = CurrentUser(id=OTHER_CITIZEN_ID, email="other@example.com", role=UserRole.citizen)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Default client authenticated as the citizen who'll own the test report."""
    app.dependency_overrides[get_current_user] = lambda: CITIZEN_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def cleanup_test_rows():
    """Remove rows the tests create (filtered by description prefix). Runs after each test."""
    yield
    db: Session = SessionLocal()
    try:
        # Find test reports first so we can delete their dependent rows.
        # Report.id is UUID after the supabase-integration merge.
        report_ids: list[uuid.UUID] = [
            r.id for r in db.scalars(
                select(Report).where(Report.description.like("E2E-RATING:%"))
            ).all()
        ]
        if report_ids:
            db.query(Rating).filter(Rating.report_id.in_(report_ids)).delete(synchronize_session=False)
            db.query(Notification).filter(Notification.report_id.in_(report_ids)).delete(synchronize_session=False)
            db.query(Report).filter(Report.id.in_(report_ids)).delete(synchronize_session=False)
            db.commit()
    finally:
        db.close()


@pytest.fixture()
def closed_status_id() -> int:
    db: Session = SessionLocal()
    try:
        row = db.scalars(select(Status).where(Status.name == "Closed")).first()
        if row is None:
            pytest.skip("Seed missing: no status row named 'Closed'")
        return row.id
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _act_as(user: CurrentUser):
    """Override the auth dep to act as the given user."""
    app.dependency_overrides[get_current_user] = lambda: user


def _create_citizen_report(client: TestClient, description: str = "E2E-RATING: complaint") -> str:
    """Returns the report id as a string (UUID format)."""
    _act_as(CITIZEN_USER)
    resp = client.post(REPORTS_PREFIX, json={"description": description})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _close_report(client: TestClient, report_id: str, closed_status_id: int) -> None:
    _act_as(OFFICER_USER)
    resp = client.patch(f"{REPORTS_PREFIX}/{report_id}/status", json={"status_id": closed_status_id})
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# POST /reports/{id}/rating
# ---------------------------------------------------------------------------

class TestPostRating:
    def test_owner_rates_closed_report_succeeds(self, client: TestClient, closed_status_id: int):
        rid = _create_citizen_report(client)
        _close_report(client, rid, closed_status_id)

        _act_as(CITIZEN_USER)
        resp = client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 5, "comment": "fast fix"})
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["stars"] == 5
        assert body["comment"] == "fast fix"
        assert body["report_id"] == rid
        assert body["citizen_id"] == str(CITIZEN_USER_ID)

    def test_409_when_report_not_closed(self, client: TestClient):
        rid = _create_citizen_report(client)

        _act_as(CITIZEN_USER)
        resp = client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 4})
        assert resp.status_code == 409
        assert "closed" in resp.json()["detail"].lower()

    def test_409_when_already_rated(self, client: TestClient, closed_status_id: int):
        rid = _create_citizen_report(client)
        _close_report(client, rid, closed_status_id)

        _act_as(CITIZEN_USER)
        first = client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 5})
        assert first.status_code == 201
        second = client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 1})
        assert second.status_code == 409
        assert "already" in second.json()["detail"].lower()

    def test_403_when_not_owner(self, client: TestClient, closed_status_id: int):
        rid = _create_citizen_report(client)
        _close_report(client, rid, closed_status_id)

        _act_as(OTHER_CITIZEN)
        resp = client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 5})
        assert resp.status_code == 403

    def test_403_when_officer_tries_to_rate(self, client: TestClient, closed_status_id: int):
        rid = _create_citizen_report(client)
        _close_report(client, rid, closed_status_id)

        _act_as(OFFICER_USER)
        resp = client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 5})
        assert resp.status_code == 403  # require_roles(citizen) excludes officer

    def test_403_when_admin_tries_to_rate(self, client: TestClient, closed_status_id: int):
        rid = _create_citizen_report(client)
        _close_report(client, rid, closed_status_id)

        _act_as(ADMIN_USER)
        resp = client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 5})
        assert resp.status_code == 403

    def test_422_when_stars_out_of_range(self, client: TestClient):
        rid = _create_citizen_report(client)
        _act_as(CITIZEN_USER)
        for bad in (0, 6, -1, 100):
            resp = client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": bad})
            assert resp.status_code == 422, f"stars={bad} should 422"

    def test_404_when_report_missing(self, client: TestClient):
        _act_as(CITIZEN_USER)
        resp = client.post(f"{REPORTS_PREFIX}/9999999/rating", json={"stars": 5})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /reports/{id}/rating
# ---------------------------------------------------------------------------

class TestGetRating:
    def test_owner_reads_own_rating(self, client: TestClient, closed_status_id: int):
        rid = _create_citizen_report(client)
        _close_report(client, rid, closed_status_id)
        _act_as(CITIZEN_USER)
        client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 4, "comment": "ok"})

        resp = client.get(f"{REPORTS_PREFIX}/{rid}/rating")
        assert resp.status_code == 200
        assert resp.json()["stars"] == 4

    def test_officer_reads_any_rating(self, client: TestClient, closed_status_id: int):
        rid = _create_citizen_report(client)
        _close_report(client, rid, closed_status_id)
        _act_as(CITIZEN_USER)
        client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 3})

        _act_as(OFFICER_USER)
        resp = client.get(f"{REPORTS_PREFIX}/{rid}/rating")
        assert resp.status_code == 200
        assert resp.json()["stars"] == 3

    def test_admin_reads_any_rating(self, client: TestClient, closed_status_id: int):
        rid = _create_citizen_report(client)
        _close_report(client, rid, closed_status_id)
        _act_as(CITIZEN_USER)
        client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 2})

        _act_as(ADMIN_USER)
        resp = client.get(f"{REPORTS_PREFIX}/{rid}/rating")
        assert resp.status_code == 200

    def test_403_when_other_citizen(self, client: TestClient, closed_status_id: int):
        rid = _create_citizen_report(client)
        _close_report(client, rid, closed_status_id)
        _act_as(CITIZEN_USER)
        client.post(f"{REPORTS_PREFIX}/{rid}/rating", json={"stars": 5})

        _act_as(OTHER_CITIZEN)
        resp = client.get(f"{REPORTS_PREFIX}/{rid}/rating")
        assert resp.status_code == 403

    def test_404_when_no_rating_yet(self, client: TestClient):
        rid = _create_citizen_report(client)
        _act_as(CITIZEN_USER)
        resp = client.get(f"{REPORTS_PREFIX}/{rid}/rating")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Status -> Closed creates an in-app notification
# ---------------------------------------------------------------------------

class TestCloseStatusCreatesNotification:
    def test_closing_a_report_queues_invitation_for_owner(self, client: TestClient, closed_status_id: int):
        rid = _create_citizen_report(client)
        rid_uuid = uuid.UUID(rid)

        # Snapshot existing notification rows for this report (should be 0)
        db: Session = SessionLocal()
        try:
            before = db.scalars(
                select(Notification).where(Notification.report_id == rid_uuid)
            ).all()
            assert len(before) == 0
        finally:
            db.close()

        _close_report(client, rid, closed_status_id)

        # Verify a new notification row was created for the citizen owner
        db = SessionLocal()
        try:
            after = db.scalars(
                select(Notification).where(Notification.report_id == rid_uuid)
            ).all()
            assert len(after) == 1
            n = after[0]
            assert n.user_id == CITIZEN_USER_ID
            assert n.is_read is False
            assert "rating" in n.message.lower()
        finally:
            db.close()

    def test_non_close_status_change_does_not_queue_notification(
        self, client: TestClient, closed_status_id: int
    ):
        rid = _create_citizen_report(client)
        rid_uuid = uuid.UUID(rid)

        # Pick a non-Closed status. Use status_id=1 (Submitted) to stay portable
        # in case "In Progress" doesn't exist.
        _act_as(OFFICER_USER)
        resp = client.patch(f"{REPORTS_PREFIX}/{rid}/status", json={"status_id": 1})
        assert resp.status_code == 200

        db: Session = SessionLocal()
        try:
            rows = db.scalars(
                select(Notification).where(Notification.report_id == rid_uuid)
            ).all()
            # No rating-invitation notification expected
            assert all("rating" not in n.message.lower() for n in rows)
        finally:
            db.close()


# ---------------------------------------------------------------------------
# GET /analytics/ratings
# ---------------------------------------------------------------------------

class TestAnalyticsRatings:
    def test_admin_can_read(self, client: TestClient):
        _act_as(ADMIN_USER)
        resp = client.get(f"{ANALYTICS_PREFIX}/ratings")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        # Each row must follow the CategoryRatingAvg schema (post-merge: was per
        # department before the Report→Department FK was removed).
        for row in body:
            assert "category_id" in row
            assert "category_name" in row
            assert "average_stars" in row
            assert "ratings_count" in row
            assert 0 <= row["average_stars"] <= 5

    def test_officer_can_read(self, client: TestClient):
        _act_as(OFFICER_USER)
        resp = client.get(f"{ANALYTICS_PREFIX}/ratings")
        assert resp.status_code == 200

    def test_citizen_forbidden(self, client: TestClient):
        _act_as(CITIZEN_USER)
        resp = client.get(f"{ANALYTICS_PREFIX}/ratings")
        assert resp.status_code == 403
