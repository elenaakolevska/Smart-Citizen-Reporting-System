"""Unit tests for report_service.export_reports filter behavior.

Pure-mock: no DB.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import app.db.base  # noqa: F401  -- registers all models
from app.services import report_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scalars_side_effect(steps: list[dict]):
    """Return a side_effect that sequentially yields different chains for each call.

    Each step is one of:
      {"first": <value>}                    — for status/category name lookups
      {"unique_all": [<rows>]}              — for the final SELECT chain
    """
    iter_steps = iter(steps)

    def _side_effect(_stmt):
        step = next(iter_steps)
        chain = MagicMock()
        if "first" in step:
            chain.first.return_value = step["first"]
        if "unique_all" in step:
            chain.unique.return_value.all.return_value = step["unique_all"]
        return chain

    return _side_effect


# ---------------------------------------------------------------------------
# export_reports
# ---------------------------------------------------------------------------

class TestExportReports:
    def test_no_filters_returns_all_rows(self):
        db = MagicMock()
        rep_a = MagicMock(); rep_a.id = 1
        rep_b = MagicMock(); rep_b.id = 2
        db.scalars.side_effect = _scalars_side_effect([{"unique_all": [rep_a, rep_b]}])

        result = report_service.export_reports(db)

        assert result == [rep_a, rep_b]
        assert db.scalars.call_count == 1

    def test_unknown_status_short_circuits_to_empty(self):
        """Typo'd status filter must NOT be silently ignored — return []."""
        db = MagicMock()
        db.scalars.side_effect = _scalars_side_effect([{"first": None}])

        result = report_service.export_reports(db, status="DoesNotExist")

        assert result == []
        # Final SELECT is never executed
        assert db.scalars.call_count == 1

    def test_unknown_category_short_circuits_to_empty(self):
        db = MagicMock()
        db.scalars.side_effect = _scalars_side_effect([{"first": None}])

        result = report_service.export_reports(db, category="DoesNotExist")

        assert result == []
        assert db.scalars.call_count == 1

    def test_known_status_runs_final_query(self):
        db = MagicMock()
        status_row = MagicMock(); status_row.id = 5
        rep = MagicMock(); rep.id = 7
        db.scalars.side_effect = _scalars_side_effect([
            {"first": status_row},          # status lookup
            {"unique_all": [rep]},          # final SELECT
        ])

        result = report_service.export_reports(db, status="Closed")

        assert result == [rep]
        assert db.scalars.call_count == 2

    def test_known_category_runs_final_query(self):
        db = MagicMock()
        cat_row = MagicMock(); cat_row.id = 1
        rep = MagicMock(); rep.id = 7
        db.scalars.side_effect = _scalars_side_effect([
            {"first": cat_row},
            {"unique_all": [rep]},
        ])

        result = report_service.export_reports(db, category="Infrastructure")

        assert result == [rep]
        assert db.scalars.call_count == 2

    def test_status_then_unknown_category_returns_empty(self):
        """Sequential filters: known status, unknown category → still []."""
        db = MagicMock()
        status_row = MagicMock(); status_row.id = 5
        db.scalars.side_effect = _scalars_side_effect([
            {"first": status_row},   # status lookup OK
            {"first": None},          # category lookup MISS -> early return
        ])

        result = report_service.export_reports(db, status="Closed", category="Bogus")

        assert result == []
        assert db.scalars.call_count == 2

    def test_date_range_passes_through_to_query(self):
        db = MagicMock()
        rep = MagicMock(); rep.id = 1
        db.scalars.side_effect = _scalars_side_effect([{"unique_all": [rep]}])

        result = report_service.export_reports(
            db,
            date_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
            date_to=datetime(2026, 12, 31, tzinfo=timezone.utc),
        )

        assert result == [rep]

    def test_returns_list_not_iterator(self):
        """Caller relies on len()/indexing — must be a materialized list."""
        db = MagicMock()
        db.scalars.side_effect = _scalars_side_effect([{"unique_all": []}])
        result = report_service.export_reports(db)
        assert isinstance(result, list)
