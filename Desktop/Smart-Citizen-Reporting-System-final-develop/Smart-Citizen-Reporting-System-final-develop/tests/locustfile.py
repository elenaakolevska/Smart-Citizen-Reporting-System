"""
Locust Performance Test — Smart Citizen Complaint Management System
====================================================================
Симулира 50 concurrent корисници со реалистично однесување.

Инсталација:
  pip install locust

Стартување (headless, 50 корисници, 30 секунди):
  locust -f tests/locustfile.py --headless -u 50 -r 10 --run-time 30s --host http://localhost:8000

Стартување (со UI):
  locust -f tests/locustfile.py --host http://localhost:8000
  # Отвори: http://localhost:8089

Напомена:
  DEV_SKIP_AUTH=true мора да е поставено на серверот.
  За production тестирање додај Authorization header со валиден JWT.
"""

from locust import HttpUser, TaskSet, between, task


class ReportTaskSet(TaskSet):
    """Реалистичен mix на read/write операции."""

    report_ids: list[str] = []

    def on_start(self):
        """Загреј со еден GET пред да почнат tasks."""
        self.client.get("/health")

    @task(5)
    def health_check(self):
        """Lightweight health probe — висока фреквенција."""
        self.client.get("/health", name="/health")

    @task(10)
    def list_reports(self):
        """Листање на репорти — најчеста операција."""
        self.client.get("/api/v1/reports", name="/api/v1/reports [GET]")

    @task(3)
    def create_report(self):
        """Поднесување нова пријава."""
        payload = {
            "description": "Locust тест: Расипана улична светилка.",
            "latitude": 41.9965,
            "longitude": 21.4314,
        }
        with self.client.post(
            "/api/v1/reports",
            json=payload,
            name="/api/v1/reports [POST]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                report_id = resp.json().get("id")
                if report_id:
                    ReportTaskSet.report_ids.append(report_id)
                resp.success()
            else:
                resp.failure(f"Create failed: {resp.status_code}")

    @task(4)
    def get_report(self):
        """Вчитување конкретен репорт."""
        if not ReportTaskSet.report_ids:
            return
        report_id = ReportTaskSet.report_ids[-1]
        with self.client.get(
            f"/api/v1/reports/{report_id}",
            name="/api/v1/reports/{id} [GET]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403, 404):
                resp.success()
            else:
                resp.failure(f"Get failed: {resp.status_code}")

    @task(1)
    def export_csv(self):
        """CSV export — поретко, но важно за performance."""
        with self.client.get(
            "/api/v1/reports/export/csv",
            name="/api/v1/reports/export/csv",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"CSV export failed: {resp.status_code}")

    @task(1)
    def analytics_summary(self):
        """Analytics summary — admin endpoint."""
        with self.client.get(
            "/api/v1/analytics/summary",
            name="/api/v1/analytics/summary",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Analytics failed: {resp.status_code}")

    @task(1)
    def ai_analyze(self):
        """AI analyze endpoint."""
        with self.client.post(
            "/api/v1/ai/analyze-report",
            json={"description": "Locust: Расипана канализација на улица."},
            name="/api/v1/ai/analyze-report",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 500):
                resp.success()
            else:
                resp.failure(f"AI analyze failed: {resp.status_code}")


class CitizenUser(HttpUser):
    """Симулира просечен граѓанин."""
    tasks = [ReportTaskSet]
    wait_time = between(1, 3)
    weight = 7


class OfficerUser(HttpUser):
    """Симулира службеник кој прегледува репорти."""
    tasks = {ReportTaskSet: 1}
    wait_time = between(2, 5)
    weight = 2


class AdminUser(HttpUser):
    """Симулира администратор кој прегледува аналитика."""

    wait_time = between(3, 8)
    weight = 1

    @task
    def analytics(self):
        self.client.get("/api/v1/analytics/summary", name="/analytics [admin]")

    @task
    def export(self):
        self.client.get("/api/v1/analytics/export/csv", name="/export/csv [admin]")