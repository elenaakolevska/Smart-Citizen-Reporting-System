"""Unit tests for rating_service and the close-status -> rating-invitation
notification trigger in report_service.update_status.

Pure-mock: no DB, no FastAPI app — runs anywhere.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

import app.db.base  # noqa: F401  -- registers all models
from app.models.notification import Notification
from app.models.report import Report as ReportModel
from app.models.status import Status as StatusModel
from app.schemas.rating import RatingCreate
from app.schemas.user import CurrentUser, UserRole
from app.services import rating_service, report_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(role: UserRole, uid=None) -> CurrentUser:
    return CurrentUser(id=uid or uuid4(), email="u@example.com", role=role)


def _report_mock(*, user_id=None, status_id=None, report_id: UUID | None = None) -> MagicMock:
    """Mock a Report row that survives ReportRead.model_validate (from_attributes)."""
    r = MagicMock()
    r.id = report_id or uuid4()
    r.description = "demo description"
    r.priority = None
    r.category_id = None
    r.status_id = status_id
    r.user_id = user_id or uuid4()
    r.latitude = None
    r.longitude = None
    r.created_at = datetime.now(timezone.utc)
    r.updated_at = datetime.now(timezone.utc)
    r.possible_duplicate_of = None
    r.ai_confirmation_text = None
    r.history_entries = []
    r.comments = []
    return r


def _status_mock(name: str, status_id: int = 5) -> MagicMock:
    s = MagicMock()
    s.id = status_id
    s.name = name
    return s


def _rating_mock(*, report_id: UUID | None = None, citizen_id=None, stars: int = 5) -> MagicMock:
    r = MagicMock()
    r.id = 1
    r.report_id = report_id or uuid4()
    r.citizen_id = citizen_id or uuid4()
    r.stars = stars
    r.comment = None
    r.created_at = datetime.now(timezone.utc)
    return r


def _scalars_first(value) -> MagicMock:
    chain = MagicMock()
    chain.first.return_value = value
    return chain


# ---------------------------------------------------------------------------
# create_rating
# ---------------------------------------------------------------------------

class TestCreateRating:
    def _payload(self, stars: int = 5, comment: str | None = "Great!") -> RatingCreate:
        return RatingCreate(stars=stars, comment=comment)

    def _db(self, *, report, status, existing_rating=None) -> MagicMock:
        db = MagicMock()

        def _get(model, _pk):
            if model is ReportModel:
                return report
            if model is StatusModel:
                return status
            return None

        db.get.side_effect = _get
        db.scalars.return_value = _scalars_first(existing_rating)

        # Mimic INSERT side-effects (autoincrement id, server_default created_at)
        # so RatingRead.model_validate(rating) succeeds.
        def _refresh(obj):
            if getattr(obj, "id", None) in (None, 0):
                obj.id = 1
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(timezone.utc)

        db.refresh.side_effect = _refresh
        return db

    def test_owner_rates_closed_report_succeeds(self):
        user = _user(UserRole.citizen)
        report = _report_mock(user_id=user.id, status_id=5)
        db = self._db(report=report, status=_status_mock("Closed"))

        result = rating_service.create_rating(
            db, report_id=report.id, rating_in=self._payload(stars=4, comment="ok"),
            current_user=user,
        )

        assert result.stars == 4
        assert result.comment == "ok"
        assert result.report_id == report.id
        assert result.citizen_id == user.id
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_404_when_report_missing(self):
        user = _user(UserRole.citizen)
        db = self._db(report=None, status=None)
        with pytest.raises(HTTPException) as exc:
            rating_service.create_rating(
                db, report_id=uuid4(), rating_in=self._payload(), current_user=user,
            )
        assert exc.value.status_code == 404

    def test_403_when_not_owner(self):
        user = _user(UserRole.citizen)
        report = _report_mock(user_id=uuid4(), status_id=5)
        db = self._db(report=report, status=_status_mock("Closed"))
        with pytest.raises(HTTPException) as exc:
            rating_service.create_rating(
                db, report_id=report.id, rating_in=self._payload(), current_user=user,
            )
        assert exc.value.status_code == 403
        db.add.assert_not_called()

    def test_409_when_status_not_closed(self):
        user = _user(UserRole.citizen)
        report = _report_mock(user_id=user.id, status_id=2)
        db = self._db(report=report, status=_status_mock("In Progress", status_id=2))
        with pytest.raises(HTTPException) as exc:
            rating_service.create_rating(
                db, report_id=report.id, rating_in=self._payload(), current_user=user,
            )
        assert exc.value.status_code == 409
        db.add.assert_not_called()

    def test_409_when_status_id_is_none(self):
        user = _user(UserRole.citizen)
        report = _report_mock(user_id=user.id, status_id=None)
        db = self._db(report=report, status=None)
        with pytest.raises(HTTPException) as exc:
            rating_service.create_rating(
                db, report_id=report.id, rating_in=self._payload(), current_user=user,
            )
        assert exc.value.status_code == 409

    def test_409_when_status_row_missing(self):
        """Defensive: status_id is set but the Status row doesn't exist."""
        user = _user(UserRole.citizen)
        report = _report_mock(user_id=user.id, status_id=99)
        db = self._db(report=report, status=None)
        with pytest.raises(HTTPException) as exc:
            rating_service.create_rating(
                db, report_id=report.id, rating_in=self._payload(), current_user=user,
            )
        assert exc.value.status_code == 409

    def test_409_when_already_rated(self):
        user = _user(UserRole.citizen)
        report = _report_mock(user_id=user.id, status_id=5)
        db = self._db(
            report=report,
            status=_status_mock("Closed"),
            existing_rating=_rating_mock(citizen_id=user.id),
        )
        with pytest.raises(HTTPException) as exc:
            rating_service.create_rating(
                db, report_id=report.id, rating_in=self._payload(), current_user=user,
            )
        assert exc.value.status_code == 409
        db.add.assert_not_called()

    def test_409_on_integrity_error_on_commit(self):
        """Concurrent insert: the unique index trips IntegrityError -> 409."""
        user = _user(UserRole.citizen)
        report = _report_mock(user_id=user.id, status_id=5)
        db = self._db(report=report, status=_status_mock("Closed"))
        db.commit.side_effect = IntegrityError("dup", {}, Exception("dup"))

        with pytest.raises(HTTPException) as exc:
            rating_service.create_rating(
                db, report_id=report.id, rating_in=self._payload(), current_user=user,
            )
        assert exc.value.status_code == 409
        db.rollback.assert_called_once()

    def test_pydantic_rejects_stars_below_1(self):
        with pytest.raises(Exception):
            RatingCreate(stars=0)

    def test_pydantic_rejects_stars_above_5(self):
        with pytest.raises(Exception):
            RatingCreate(stars=6)

    def test_pydantic_accepts_optional_comment(self):
        rc = RatingCreate(stars=3)
        assert rc.comment is None


# ---------------------------------------------------------------------------
# get_rating
# ---------------------------------------------------------------------------

class TestGetRating:
    def _db(self, *, report, rating=None) -> MagicMock:
        db = MagicMock()
        db.get.return_value = report
        db.scalars.return_value = _scalars_first(rating)
        return db

    def test_owner_reads_own_rating(self):
        user = _user(UserRole.citizen)
        report = _report_mock(user_id=user.id)
        db = self._db(report=report, rating=_rating_mock(citizen_id=user.id))
        result = rating_service.get_rating(db, report_id=report.id, current_user=user)
        assert result.stars == 5

    def test_citizen_cannot_read_other_users_rating(self):
        user = _user(UserRole.citizen)
        report = _report_mock(user_id=uuid4())
        db = self._db(report=report, rating=_rating_mock())
        with pytest.raises(HTTPException) as exc:
            rating_service.get_rating(db, report_id=report.id, current_user=user)
        assert exc.value.status_code == 403

    def test_officer_reads_any_rating(self):
        officer = _user(UserRole.officer)
        report = _report_mock(user_id=uuid4())
        db = self._db(report=report, rating=_rating_mock())
        result = rating_service.get_rating(db, report_id=report.id, current_user=officer)
        assert result.stars == 5

    def test_admin_reads_any_rating(self):
        admin = _user(UserRole.admin)
        report = _report_mock(user_id=uuid4())
        db = self._db(report=report, rating=_rating_mock())
        result = rating_service.get_rating(db, report_id=report.id, current_user=admin)
        assert result.stars == 5

    def test_404_when_report_missing(self):
        with pytest.raises(HTTPException) as exc:
            rating_service.get_rating(
                self._db(report=None), report_id=uuid4(), current_user=_user(UserRole.admin),
            )
        assert exc.value.status_code == 404

    def test_404_when_no_rating_for_report(self):
        admin = _user(UserRole.admin)
        report = _report_mock(user_id=uuid4())
        db = self._db(report=report, rating=None)
        with pytest.raises(HTTPException) as exc:
            rating_service.get_rating(db, report_id=report.id, current_user=admin)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# average_ratings_by_category (was by department before the supabase merge
# removed the Report→Department FK)
# ---------------------------------------------------------------------------

class TestAverageByCategory:
    def _exec_returning(self, rows: list) -> MagicMock:
        db = MagicMock()
        execute_result = MagicMock()
        execute_result.all.return_value = rows
        db.execute.return_value = execute_result
        return db

    def test_returns_aggregates_per_category(self):
        row1 = MagicMock()
        row1.category_id = 1
        row1.category_name = "Infrastructure"
        row1.avg_stars = 4.5
        row1.ratings_count = 10
        row2 = MagicMock()
        row2.category_id = 2
        row2.category_name = "Environment"
        row2.avg_stars = 3.25
        row2.ratings_count = 4

        result = rating_service.average_ratings_by_category(
            self._exec_returning([row1, row2])
        )
        assert len(result) == 2
        assert result[0].category_name == "Infrastructure"
        assert result[0].average_stars == 4.5
        assert result[0].ratings_count == 10
        assert result[1].category_name == "Environment"
        assert result[1].average_stars == 3.25
        assert result[1].ratings_count == 4

    def test_returns_empty_list_when_no_ratings(self):
        result = rating_service.average_ratings_by_category(self._exec_returning([]))
        assert result == []

    def test_average_is_rounded_to_two_decimals(self):
        row = MagicMock()
        row.category_id = 1
        row.category_name = "X"
        row.avg_stars = 4.123456
        row.ratings_count = 7
        result = rating_service.average_ratings_by_category(self._exec_returning([row]))
        assert result[0].average_stars == 4.12


# ---------------------------------------------------------------------------
# update_status -> rating-invitation notification (CR-06)
# ---------------------------------------------------------------------------

class TestCloseTransitionNotifies:
    def _status_in(self, status_id: int) -> MagicMock:
        m = MagicMock()
        m.status_id = status_id
        return m

    def _db_returning(self, *, report: MagicMock, status_name: str) -> MagicMock:
        db = MagicMock()

        def _get(model, _pk):
            if model is ReportModel:
                return report
            if model is StatusModel:
                return _status_mock(status_name)
            return None

        db.get.side_effect = _get
        return db

    def test_submitted_to_closed_queues_notification(self):
        officer = _user(UserRole.officer)
        report = _report_mock(user_id=uuid4(), status_id=1)
        db = self._db_returning(report=report, status_name="Closed")

        report_service.update_status(
            db, report_id=report.id, status_in=self._status_in(5), current_user=officer,
        )

        added = [c.args[0] for c in db.add.call_args_list]
        notifs = [a for a in added if isinstance(a, Notification)]
        assert len(notifs) == 1
        n = notifs[0]
        assert n.user_id == report.user_id
        assert n.report_id == report.id
        assert "rating" in n.message.lower()
        assert n.is_read is False

    def test_transition_to_non_closed_does_not_notify(self):
        officer = _user(UserRole.officer)
        report = _report_mock(user_id=uuid4(), status_id=1)
        db = self._db_returning(report=report, status_name="In Progress")

        report_service.update_status(
            db, report_id=report.id, status_in=self._status_in(2), current_user=officer,
        )

        added = [c.args[0] for c in db.add.call_args_list]
        assert all(not isinstance(a, Notification) for a in added)

    def test_no_change_no_history_no_notification(self):
        officer = _user(UserRole.officer)
        report = _report_mock(user_id=uuid4(), status_id=5)
        # status->Status lookup not needed because status_changed is False
        db = MagicMock()
        db.get.return_value = report

        report_service.update_status(
            db, report_id=report.id, status_in=self._status_in(5), current_user=officer,
        )

        db.add.assert_not_called()
