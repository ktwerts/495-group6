"""End-to-end tests that run across modules, starting from `flask seed`."""

from datetime import date, timedelta

import pytest

from app.scheduling import service as scheduling

ADMIN_PASSWORD = "seeded-manager-pass"
EMPLOYEE_PASSWORD = "seeded-employee-pass"


@pytest.fixture
def seeded(app, monkeypatch):
    monkeypatch.setenv("SHIFTWISE_ADMIN_PASSWORD", ADMIN_PASSWORD)
    monkeypatch.setenv("SHIFTWISE_EMPLOYEE_PASSWORD", EMPLOYEE_PASSWORD)
    result = app.test_cli_runner().invoke(args=["seed"])
    assert result.exit_code == 0, result.output
    return app


def login(app, username, password):
    client = app.test_client()
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return client


def test_seeded_manager_can_train_and_forecast(seeded):
    manager = login(seeded, "manager", ADMIN_PASSWORD)

    assert manager.get("/forecast").status_code == 200
    metrics = manager.post("/api/forecast/train").get_json()
    assert metrics["method"] == "random_forest"
    assert metrics["history_days"] == 180

    body = manager.get("/api/forecast?days=14").get_json()
    assert body["metrics"] == metrics
    assert len(body["days"]) == 14
    assert all(day["predicted_staff_needed"] >= 1 for day in body["days"])


def test_seeded_employee_cannot_see_forecast(seeded):
    employee = login(seeded, "employee", EMPLOYEE_PASSWORD)
    assert employee.get("/forecast").status_code == 403
    assert employee.get("/api/forecast").status_code == 403


def test_forecast_asks_scheduling_for_each_day(seeded, monkeypatch):
    start = date(2026, 12, 7)
    scheduled = {(start + timedelta(days=n)).isoformat(): n for n in range(7)}
    asked = []

    def count_scheduled_staff(on_date):
        asked.append(on_date)
        return scheduled[on_date]

    monkeypatch.setattr(scheduling, "count_scheduled_staff", count_scheduled_staff)
    manager = login(seeded, "manager", ADMIN_PASSWORD)
    days = manager.get(f"/api/forecast?start={start}&days=7").get_json()["days"]

    assert asked == list(scheduled)
    for day in days:
        assert day["scheduled_staff"] == scheduled[day["date"]]
        assert day["gap"] == day["predicted_staff_needed"] - day["scheduled_staff"]


@pytest.mark.skip(reason="TODO: needs absences, recommendations and approval from Scheduling")
def test_approved_replacement_closes_forecast_gap(seeded):
    """Owners: Lead Architect + Integration Lead.

    Report an absence -> shift opens -> recommend replacements -> manager approves ->
    the forecast for that day shows one more scheduled staff member and a smaller gap.
    """
