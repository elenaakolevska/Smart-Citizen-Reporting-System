"""
Integration + E2E Tests — /api/v1/reports
==========================================
Вкупно: 37 тестови

  Оригинални (01-15): основни CRUD тестови
  E2E (16-25):        citizen workflow, коментари, export, дупликати
  CR (26-37):         priority, notifications, регресија

Стартување:
  python -m pytest tests/test_reports_api.py -v
  python -m pytest tests/test_reports_api.py -v --cov=app --cov-report=term-missing
"""

from __future__ import annotations

import os
import uuid
import csv
import io
from collections.abc import Generator
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# ── Мора да биде ПРЕД сите app imports ────────────────────────────────────────
os.environ["DEV_SKIP_AUTH"]          = "true"
os.environ["AI_ENABLED"]             = "false"
os.environ["AI_PRELOAD_ON_STARTUP"]  = "false"

from app.core.config import get_settings       # noqa: E402
get_settings.cache_clear()

from app.db.session import SessionLocal        # noqa: E402
from app.main import app                       # noqa: E402
from app.models.report import Report           # noqa: E402
from app.models.notification import Notification  # noqa: E402
from app.schemas.user import CurrentUser, UserRole  # noqa: E402
from app.utils.dependencies import DEV_USER, get_current_user  # noqa: E402

# ── Константи ─────────────────────────────────────────────────────────────────
PREFIX           = "/api/v1/reports"
ANALYTICS_PREFIX = "/api/v1/analytics"
DEV_USER_ID      = str(DEV_USER.id)  # "12345678-1234-1234-1234-123456789012"

CITIZEN_USER = CurrentUser(
    id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
    email="citizen_test@example.com",
    role=UserRole.citizen,
)

OFFICER_USER = CurrentUser(
    id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    email="officer@example.com",
    role=UserRole.officer,
)

VALID_PAYLOAD = {
    "description": "Скршена улична светилка кај плоштадот.",
}

VALID_PAYLOAD_WITH_LOCATION = {
    "description": "Расипан водовод на улица Питу Гули.",
    "latitude": 41.9965,
    "longitude": 21.4314,
}

_CLEANUP_PREFIXES = [
    "Скршена улична светилка%",
    "Расипан водовод%",
    "Тест:%",
    "PATCH тест%",
    "Ќе биде избришан%",
    "Долг опис%",
    "Officer%",
    "E2E%",
    "Дупликат%",
    "CR%",
    "Priority%",
    "Notification%",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_all_tests():
    """Ги рандира сите тестови еден по еден."""
    import pytest as _pt
    _pt.main(["tests/test_reports_api.py", "-v"])


def _restore_dev_user():
    app.dependency_overrides[get_current_user] = lambda: DEV_USER


def _override(user: CurrentUser):
    app.dependency_overrides[get_current_user] = lambda: user


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    _restore_dev_user()
    with TestClient(app) as c:
        yield c
    _restore_dev_user()


@pytest.fixture(autouse=True)
def cleanup_reports():
    yield
    db: Session = SessionLocal()
    try:
        from sqlalchemy import or_
        conditions = [Report.description.like(p) for p in _CLEANUP_PREFIXES]
        db.query(Report).filter(or_(*conditions)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _create(client: TestClient, payload: dict | None = None) -> dict:
    resp = client.post(PREFIX, json=payload or VALID_PAYLOAD)
    assert resp.status_code == 201, f"Неуспешно креирање: {resp.text}"
    return resp.json()


# ═════════════════════════════════════════════════════════════════════════════
# ОРИГИНАЛНИ 15 ТЕСТОВИ
# ═════════════════════════════════════════════════════════════════════════════

def test_01_create_report_minimal_payload(client: TestClient):
    resp = client.post(PREFIX, json=VALID_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["description"] == VALID_PAYLOAD["description"]
    assert "id" in body
    assert "user_id" in body
    assert "created_at" in body
    assert body["category_id"] is None
    assert body["status_id"] is None


def test_02_create_report_with_location(client: TestClient):
    resp = client.post(PREFIX, json=VALID_PAYLOAD_WITH_LOCATION)
    assert resp.status_code == 201
    body = resp.json()
    assert body["latitude"] == pytest.approx(41.9965)
    assert body["longitude"] == pytest.approx(21.4314)


def test_03_create_report_empty_description_fails(client: TestClient):
    resp = client.post(PREFIX, json={"description": ""})
    assert resp.status_code == 422
    fields = [e["loc"][-1] for e in resp.json()["detail"]]
    assert "description" in fields


def test_04_create_report_missing_description_fails(client: TestClient):
    resp = client.post(PREFIX, json={"latitude": 41.99})
    assert resp.status_code == 422


def test_05_list_reports_admin_sees_all(client: TestClient):
    created = _create(client)
    resp = client.get(PREFIX)
    assert resp.status_code == 200
    assert created["id"] in [r["id"] for r in resp.json()]


def test_06_get_report_by_id(client: TestClient):
    created = _create(client)
    resp = client.get(f"{PREFIX}/{created['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["description"] == VALID_PAYLOAD["description"]
    assert body["user_id"] == DEV_USER_ID


def test_07_get_report_not_found(client: TestClient):
    resp = client.get(f"{PREFIX}/999999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_08_patch_report_description(client: TestClient):
    created = _create(client, {"description": "PATCH тест: оригинален опис."})
    resp = client.patch(f"{PREFIX}/{created['id']}", json={"description": "PATCH тест: ажуриран опис."})
    assert resp.status_code == 200
    assert resp.json()["description"] == "PATCH тест: ажуриран опис."


def test_09_patch_admin_can_change_status_and_category(client: TestClient):
    created = _create(client, {"description": "Тест: admin status patch."})
    resp = client.patch(f"{PREFIX}/{created['id']}", json={"status_id": 1, "category_id": 1})
    assert resp.status_code == 200
    assert resp.json()["status_id"] == 1
    assert resp.json()["category_id"] == 1


def test_10_delete_report(client: TestClient):
    created = _create(client, {"description": "Ќе биде избришан."})
    assert client.delete(f"{PREFIX}/{created['id']}").status_code == 204
    assert client.get(f"{PREFIX}/{created['id']}").status_code == 404


def test_11_get_report_forbidden_for_citizen(client: TestClient):
    db: Session = SessionLocal()
    try:
        report = Report(description="Тест: туѓ репорт за citizen.", user_id=DEV_USER.id)
        db.add(report)
        db.commit()
        db.refresh(report)
        report_id = report.id
    finally:
        db.close()

    _override(CITIZEN_USER)
    try:
        resp = client.get(f"{PREFIX}/{report_id}")
        assert resp.status_code == 403
    finally:
        _restore_dev_user()


def test_12_citizen_cannot_patch_foreign_report(client: TestClient):
    db: Session = SessionLocal()
    try:
        report = Report(description="Тест: citizen patch туѓ.", user_id=DEV_USER.id)
        db.add(report)
        db.commit()
        db.refresh(report)
        report_id = report.id
    finally:
        db.close()

    _override(CITIZEN_USER)
    try:
        resp = client.patch(f"{PREFIX}/{report_id}", json={"description": "обид."})
        assert resp.status_code == 403
    finally:
        _restore_dev_user()


def test_13_officer_can_see_all_reports(client: TestClient):
    created = _create(client, {"description": "Officer тест: листање."})

    _override(OFFICER_USER)
    try:
        resp = client.get(PREFIX)
        assert resp.status_code == 200
        assert created["id"] in [r["id"] for r in resp.json()]
    finally:
        _restore_dev_user()


def test_14_create_report_max_length_description(client: TestClient):
    assert client.post(PREFIX, json={"description": "Долг опис: " + "а" * 4989}).status_code == 201
    assert client.post(PREFIX, json={"description": "Долг опис: " + "а" * 4990}).status_code == 422


def test_15_patch_nonexistent_report_returns_404(client: TestClient):
    resp = client.patch(f"{PREFIX}/999999", json={"description": "Тест: patch непостоечки."})
    assert resp.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
# E2E ТЕСТОВИ (16-25)
# ═════════════════════════════════════════════════════════════════════════════

def test_16_citizen_submit_report_with_location_verified_in_db(client: TestClient):
    payload = {"description": "E2E: Оштетен тротоар.", "latitude": 41.9981, "longitude": 21.4254}
    resp = client.post(PREFIX, json=payload)
    assert resp.status_code == 201

    db: Session = SessionLocal()
    try:
        report = db.get(Report, resp.json()["id"])
        assert report.latitude == pytest.approx(41.9981)
        assert report.longitude == pytest.approx(21.4254)
        assert str(report.user_id) == DEV_USER_ID
    finally:
        db.close()


def test_17_citizen_cannot_see_foreign_report(client: TestClient):
    created = _create(client, {"description": "E2E: Репорт на admin."})
    _override(CITIZEN_USER)
    try:
        assert client.get(f"{PREFIX}/{created['id']}").status_code == 403
    finally:
        _restore_dev_user()


def test_18_status_timeline_recorded_on_patch(client: TestClient):
    created = _create(client, {"description": "E2E: Status timeline тест."})
    resp = client.patch(f"{PREFIX}/{created['id']}", json={"status_id": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["history_entries"]) >= 1
    assert 1 in [h["status_id"] for h in body["history_entries"]]


def test_19_officer_post_comment_visible_in_get(client: TestClient):
    created = _create(client, {"description": "E2E: Репорт за коментар."})

    _override(OFFICER_USER)
    try:
        comment_resp = client.post(
            f"{PREFIX}/{created['id']}/comments",
            json={"content": "E2E: Офицерски коментар."},
        )
        assert comment_resp.status_code == 201
        comment_id = comment_resp.json()["id"]
    finally:
        _restore_dev_user()

    get_resp = client.get(f"{PREFIX}/{created['id']}")
    assert comment_id in [c["id"] for c in get_resp.json()["comments"]]


def test_20_officer_export_csv_valid(client: TestClient):
    resp = client.get(f"{ANALYTICS_PREFIX}/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    rows = list(csv.reader(io.StringIO(resp.text)))
    assert len(rows) >= 1
    assert "ID" in rows[0]


def test_21_analytics_summary_returns_expected_keys(client: TestClient):
    resp = client.get(f"{ANALYTICS_PREFIX}/summary")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("kpis", "categoryData", "pieData", "monthlyData", "resolutionRate"):
        assert key in body
    for key in ("total", "resolved", "avgTime", "activeCitizens"):
        assert key in body["kpis"]


def test_22_duplicate_detection_sets_flag(client: TestClient):
    payload = {
        "description": "E2E: Дупликат — расипан хидрант.",
        "latitude": 41.9950,
        "longitude": 21.4300,
    }
    first = _create(client, payload)
    second = client.post(PREFIX, json=payload)
    assert second.status_code == 201
    assert second.json()["possible_duplicate_of"] == first["id"]


def test_23_report_create_with_title(client: TestClient):
    resp = client.post(PREFIX, json={"title": "E2E: Наслов", "description": "E2E: Опис со наслов."})
    assert resp.status_code == 201


def test_24_patch_status_endpoint_officer(client: TestClient):
    created = _create(client, {"description": "E2E: Status endpoint тест."})

    _override(OFFICER_USER)
    try:
        resp = client.patch(f"{PREFIX}/{created['id']}/status", json={"status_id": 1})
        assert resp.status_code == 200
        assert resp.json()["status_id"] == 1
        assert len(resp.json()["history_entries"]) >= 1
    finally:
        _restore_dev_user()


def test_25_citizen_list_sees_only_own_reports(client: TestClient):
    _create(client, {"description": "E2E: Admin репорт."})

    _override(CITIZEN_USER)
    try:
        resp = client.get(PREFIX)
        assert resp.status_code == 200
        for r in resp.json():
            assert r["user_id"] == str(CITIZEN_USER.id)
    finally:
        _restore_dev_user()

def test_26_officer_can_patch_priority(client: TestClient):
    created = _create(client, {"description": "E2E: priority patch by officer."})
    report_id = created["id"]

    app.dependency_overrides[get_current_user] = lambda: OFFICER_USER
    try:
        resp = client.patch(
            f"{PREFIX}/{report_id}/priority",
            json={"priority": "Итен"},
        )
        assert resp.status_code == 200
        assert resp.json()["priority"] == "Итен"
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER


def test_27_citizen_cannot_patch_priority(client: TestClient):
    created = _create(client, {"description": "E2E: citizen cannot patch priority."})
    report_id = created["id"]

    app.dependency_overrides[get_current_user] = lambda: CITIZEN_USER
    try:
        resp = client.patch(
            f"{PREFIX}/{report_id}/priority",
            json={"priority": "Висок"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER


# ═════════════════════════════════════════════════════════════════════════════


def test_266_cr02_new_report_priority_field_exists_in_response(client: TestClient):
    """
    CR-02: Нова пријава враќа priority поле во response.
    При креирање priority е None (AI е исклучен во тестови).
    Полето мора да постои во response структурата.
    """
    resp = client.post(PREFIX, json={"description": "CR: Priority field проверка."})
    assert resp.status_code == 201
    assert "priority" in resp.json()


def test_277_cr02_priority_verified_in_db_after_manual_patch(client: TestClient):
    """
    CR-02: PATCH /{id}/priority го зачувува priority во DB.
    Проверуваме директно во базата дека вредноста е зачувана.
    """
    created = _create(client, {"description": "CR: Priority DB verify."})
    report_id = created["id"]

    resp = client.patch(f"{PREFIX}/{report_id}/priority", json={"priority": "Висок"})
    assert resp.status_code == 200
    assert resp.json()["priority"] == "Висок"

    db: Session = SessionLocal()
    try:
        report = db.get(Report, report_id)
        assert report.priority == "Висок"
    finally:
        db.close()


def test_28_cr02_officer_can_patch_priority(client: TestClient):
    """
    CR-02: Officer може да го смени priority.
    PATCH /{id}/priority е дозволен за officer и admin.
    """
    created = _create(client, {"description": "CR: Officer priority patch."})
    report_id = created["id"]

    _override(OFFICER_USER)
    try:
        resp = client.patch(f"{PREFIX}/{report_id}/priority", json={"priority": "Итен"})
        assert resp.status_code == 200
        assert resp.json()["priority"] == "Итен"
    finally:
        _restore_dev_user()


def test_29_cr02_citizen_cannot_patch_priority(client: TestClient):
    """
    CR-02: Citizen добива 403 при обид за PATCH priority.
    require_roles(officer, admin) го блокира citizen.
    """
    created = _create(client, {"description": "CR: Citizen priority 403."})
    report_id = created["id"]

    _override(CITIZEN_USER)
    try:
        resp = client.patch(f"{PREFIX}/{report_id}/priority", json={"priority": "Низок"})
        assert resp.status_code == 403
    finally:
        _restore_dev_user()


def test_30_cr02_priority_invalid_value_returns_422(client: TestClient):
    """
    CR-02: Priority мора да биде еден од: Низок, Среден, Висок, Итен.
    Невалидна вредност враќа 422.
    """
    created = _create(client, {"description": "CR: Invalid priority."})
    resp = client.patch(f"{PREFIX}/{created['id']}/priority", json={"priority": "InvalidValue"})
    assert resp.status_code == 422


def test_31_cr02_all_valid_priority_values_accepted(client: TestClient):
    """
    CR-02: Сите четири валидни priority вредности се прифатени.
    """
    for priority in ["Низок", "Среден", "Висок", "Итен"]:
        created = _create(client, {"description": f"CR: Priority {priority} тест."})
        resp = client.patch(f"{PREFIX}/{created['id']}/priority", json={"priority": priority})
        assert resp.status_code == 200, f"Priority '{priority}' треба да биде валиден"
        assert resp.json()["priority"] == priority


def test_32_cr_notification_created_on_comment(client: TestClient):
    """
    CR: Кога officer додава коментар на репорт на DEV_USER,
    нотификација се креира во notifications табела за report owner.
    notification_service.create_comment_notification се повикува од сервисот.
    """
    created = _create(client, {"description": "CR: Notification on comment."})
    report_id = created["id"]
    owner_id = DEV_USER.id

    # Брои нотификации пред коментар
    db: Session = SessionLocal()
    try:
        before = db.query(Notification).filter(
            Notification.report_id == report_id,
            Notification.user_id == owner_id,
        ).count()
    finally:
        db.close()

    # Officer додава коментар
    _override(OFFICER_USER)
    try:
        resp = client.post(
            f"{PREFIX}/{report_id}/comments",
            json={"content": "CR: Офицерски коментар за нотификација."},
        )
        assert resp.status_code == 201
    finally:
        _restore_dev_user()

    # Провери дека нотификација е додадена
    db = SessionLocal()
    try:
        after = db.query(Notification).filter(
            Notification.report_id == report_id,
            Notification.user_id == owner_id,
        ).count()
        assert after == before + 1, "Нотификацијата мора да се зачува по коментар"
    finally:
        db.close()


def test_33_cr_no_self_notification_on_comment(client: TestClient):
    """
    CR: Кога admin коментира на свој репорт,
    нотификација НЕ се креира (commenter == owner).
    notification_service го проверува ова со: if report.user_id == commenter_user_id: return
    """
    created = _create(client, {"description": "CR: No self notification."})
    report_id = created["id"]

    db: Session = SessionLocal()
    try:
        before = db.query(Notification).filter(
            Notification.report_id == report_id,
        ).count()
    finally:
        db.close()

    # Admin коментира на свој репорт
    resp = client.post(
        f"{PREFIX}/{report_id}/comments",
        json={"content": "CR: Admin self comment."},
    )
    assert resp.status_code == 201

    db = SessionLocal()
    try:
        after = db.query(Notification).filter(
            Notification.report_id == report_id,
        ).count()
        assert after == before, "Нотификација НЕ смее да се креира кога owner == commenter"
    finally:
        db.close()


def test_34_cr_status_change_logged_in_history(client: TestClient):
    """
    CR-08 регресија: PATCH status преку /status endpoint логира history.
    Проверуваме дека history_entries содржи нов запис по промена.
    """
    created = _create(client, {"description": "CR: History on status change."})
    report_id = created["id"]

    _override(OFFICER_USER)
    try:
        resp = client.patch(f"{PREFIX}/{report_id}/status", json={"status_id": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status_id"] == 2
        assert any(h["status_id"] == 2 for h in body["history_entries"])
    finally:
        _restore_dev_user()


def test_35_cr_patch_priority_does_not_affect_status(client: TestClient):
    """
    CR регресија: PATCH priority не го менува status_id.
    Изолирана промена на едно поле не смее да влијае на друго.
    """
    created = _create(client, {"description": "CR: Priority isolation."})
    report_id = created["id"]

    # Прво постави status
    client.patch(f"{PREFIX}/{report_id}", json={"status_id": 1})

    # Потоа смени priority
    resp = client.patch(f"{PREFIX}/{report_id}/priority", json={"priority": "Среден"})
    assert resp.status_code == 200
    assert resp.json()["status_id"] == 1, "status_id не смее да се промени по priority patch"
    assert resp.json()["priority"] == "Среден"


def test_36_regression_qa1_create_and_get(client: TestClient):
    """
    QA1 Регресија: Основен create + get flow е непроменет.
    """
    created = _create(client, {"description": "CR: QA1 регресија."})
    resp = client.get(f"{PREFIX}/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["description"] == "CR: QA1 регресија."





if __name__ == "__main__":
    run_all_tests()


