"""Unit tests for report_service.

The DB session and Report model are replaced with MagicMocks so no real
database or SQLAlchemy instrumentation is needed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import app.db.base
from app.schemas.user import CurrentUser, UserRole
from app.services import report_service


def _make_user(role: UserRole, uid=None) -> CurrentUser:
    return CurrentUser(id=uid or uuid4(), email="test@example.com", role=role)


def _make_report(user_id=None, report_id: int = 1) -> MagicMock:
    r = MagicMock()
    r.id = report_id
    r.description = "Broken streetlight"
    r.category_id = None
    r.status_id = None
    r.user_id = user_id or uuid4()
    r.latitude = None
    r.longitude = None
    r.created_at = datetime.now(timezone.utc)
    return r


def _db(report=None) -> MagicMock:
    """Return a mock Session with db.get() pre-configured."""
    db = MagicMock()
    db.get.return_value = report
    return db


def _report_in(**fields) -> MagicMock:
    """Mock a ReportUpdate with model_dump returning only the given fields."""
    m = MagicMock()
    m.model_dump.return_value = fields
    return m


def _priority_in(priority: str) -> MagicMock:
    m = MagicMock()
    m.priority = priority
    return m


class TestGetReport:
    def test_citizen_gets_own_report(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=user.id)
        result = report_service.get_report(_db(report), report_id=1, current_user=user)
        assert result.id == report.id

    def test_citizen_cannot_get_other_report(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=uuid4())
        with pytest.raises(HTTPException) as exc:
            report_service.get_report(_db(report), report_id=1, current_user=user)
        assert exc.value.status_code == 403

    def test_officer_can_get_any_report(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=uuid4())
        result = report_service.get_report(
            _db(report), report_id=1, current_user=officer
        )
        assert result.id == report.id

    def test_admin_can_get_any_report(self):
        admin = _make_user(UserRole.admin)
        report = _make_report(user_id=uuid4())
        result = report_service.get_report(_db(report), report_id=1, current_user=admin)
        assert result.id == report.id

    def test_missing_report_raises_404(self):
        user = _make_user(UserRole.citizen)
        with pytest.raises(HTTPException) as exc:
            report_service.get_report(_db(None), report_id=99, current_user=user)
        assert exc.value.status_code == 404


class TestUpdateReport:
    def test_citizen_updates_own_report_description(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=user.id)
        db = _db(report)

        report_service.update_report(
            db,
            report_id=1,
            report_in=_report_in(description="New text"),
            current_user=user,
        )

        assert report.description == "New text"
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(report)

    def test_citizen_cannot_update_other_report(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=uuid4())
        with pytest.raises(HTTPException) as exc:
            report_service.update_report(
                _db(report),
                report_id=1,
                report_in=_report_in(description="x"),
                current_user=user,
            )
        assert exc.value.status_code == 403

    def test_citizen_cannot_set_status_or_category(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=user.id)
        db = _db(report)

        report_service.update_report(
            db,
            report_id=1,
            report_in=_report_in(status_id=2, category_id=3),
            current_user=user,
        )

        # setattr must NOT have been called with these fields
        assert report.status_id is None
        assert report.category_id is None

    def test_officer_can_set_status_and_category(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=uuid4())
        db = _db(report)

        report_service.update_report(
            db,
            report_id=1,
            report_in=_report_in(status_id=2, category_id=3),
            current_user=officer,
        )

        assert report.status_id == 2
        assert report.category_id == 3

    def test_missing_report_raises_404(self):
        user = _make_user(UserRole.citizen)
        with pytest.raises(HTTPException) as exc:
            report_service.update_report(
                _db(None),
                report_id=99,
                report_in=_report_in(description="x"),
                current_user=user,
            )
        assert exc.value.status_code == 404


class TestDeleteReport:
    def test_citizen_deletes_own_report(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=user.id)
        db = _db(report)
        report_service.delete_report(db, report_id=1, current_user=user)
        db.delete.assert_called_once_with(report)
        db.commit.assert_called_once()

    def test_citizen_cannot_delete_other_report(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=uuid4())
        with pytest.raises(HTTPException) as exc:
            report_service.delete_report(_db(report), report_id=1, current_user=user)
        assert exc.value.status_code == 403

    def test_officer_cannot_delete_any_report(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=officer.id)  # even their own
        with pytest.raises(HTTPException) as exc:
            report_service.delete_report(_db(report), report_id=1, current_user=officer)
        assert exc.value.status_code == 403

    def test_admin_deletes_any_report(self):
        admin = _make_user(UserRole.admin)
        report = _make_report(user_id=uuid4())
        db = _db(report)
        report_service.delete_report(db, report_id=1, current_user=admin)
        db.delete.assert_called_once_with(report)

    def test_missing_report_raises_404(self):
        admin = _make_user(UserRole.admin)
        with pytest.raises(HTTPException) as exc:
            report_service.delete_report(_db(None), report_id=99, current_user=admin)
        assert exc.value.status_code == 404


class TestUpdateStatus:
    def _status_in(self, status_id: int) -> MagicMock:
        m = MagicMock()
        m.status_id = status_id
        return m

    def test_officer_changes_status_records_history(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=uuid4())
        report.status_id = 1
        db = _db(report)

        report_service.update_status(db, report_id=1, status_in=self._status_in(2), current_user=officer)

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.old_status_id == 1
        assert added.status_id == 2
        assert added.changed_by_user_id == officer.id
        assert report.status_id == 2
        db.commit.assert_called_once()

    def test_no_history_when_status_unchanged(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=uuid4())
        report.status_id = 3
        db = _db(report)

        report_service.update_status(db, report_id=1, status_in=self._status_in(3), current_user=officer)

        db.add.assert_not_called()

    def test_update_report_records_history_on_status_change(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=uuid4())
        report.status_id = 1
        db = _db(report)

        report_service.update_report(
            db, report_id=1, report_in=_report_in(status_id=2), current_user=officer
        )

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.old_status_id == 1
        assert added.status_id == 2

    def test_update_report_no_history_when_status_not_in_payload(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=uuid4())
        report.status_id = 1
        db = _db(report)

        report_service.update_report(
            db, report_id=1, report_in=_report_in(description="New text"), current_user=officer
        )

        db.add.assert_not_called()

    def test_missing_report_raises_404(self):
        officer = _make_user(UserRole.officer)
        with pytest.raises(HTTPException) as exc:
            report_service.update_status(_db(None), report_id=99, status_in=self._status_in(1), current_user=officer)
        assert exc.value.status_code == 404


class TestListReports:
    def test_citizen_sees_only_own_reports(self):
        user = _make_user(UserRole.citizen)
        own = _make_report(user_id=user.id, report_id=1)
        db = MagicMock()
        db.scalars.return_value.all.return_value = [own]

        results = report_service.list_reports(db, current_user=user)

        assert len(results) == 1
        assert results[0].user_id == user.id

    def test_admin_sees_all_reports(self):
        admin = _make_user(UserRole.admin)
        r1 = _make_report(user_id=uuid4(), report_id=1)
        r2 = _make_report(user_id=uuid4(), report_id=2)
        db = MagicMock()
        db.scalars.return_value.all.return_value = [r1, r2]

        results = report_service.list_reports(db, current_user=admin)
        assert len(results) == 2


class TestUpdatePriority:
    def test_officer_can_update_priority(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=uuid4())
        report.priority = None
        db = _db(report)

        result = report_service.update_priority(
            db,
            report_id=1,
            priority_in=_priority_in("Висок"),
            current_user=officer,
        )

        assert report.priority == "Висок"
        assert result.priority == "Висок"
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(report)


class TestRunReportAiPipelinePriority:
    def test_pipeline_does_not_overwrite_existing_priority(self, monkeypatch):
        report = MagicMock()
        report.id = 1
        report.description = "Оштетен пат"
        report.category_id = 1
        report.priority = "Итен"
        report.possible_duplicate_of = None

        fake_db = MagicMock()
        fake_db.get.return_value = report
        fake_db.scalars.return_value.all.return_value = []

        monkeypatch.setattr(report_service, "SessionLocal", lambda: fake_db)
        monkeypatch.setattr(
            report_service,
            "get_settings",
            lambda: MagicMock(
                ai_enabled=True,
                ai_min_confidence=0.5,
                ai_default_category_name=None,
                ai_confirmation_comment_user_id=None,
            ),
        )
        monkeypatch.setattr(report_service, "generate_confirmation_message", lambda *args, **kwargs: None)
        monkeypatch.setattr(report_service, "generate_confirmation_mk", lambda *args, **kwargs: "mk")

        called = {"assign": False}

        def _assign_priority(_text, _history):
            called["assign"] = True
            return "Низок"

        monkeypatch.setattr(report_service, "assign_priority", _assign_priority)

        report_service.run_report_ai_pipeline(1)

        assert called["assign"] is False
        assert report.priority == "Итен"
