"""End-to-end tests that run across modules, starting from `flask seed`."""

from datetime import date, timedelta

import pytest

from app.forecasting.history import generate_sample_history, save_history
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


def not_implemented(*args):
    raise NotImplementedError


def test_forecast_gets_scheduled_counts_for_the_range_in_one_call(seeded, monkeypatch):
    start = date(2026, 12, 7)
    scheduled = {(start + timedelta(days=n)).isoformat(): n for n in range(7)}
    asked = []

    def count_scheduled_staff_between(first, last):
        asked.append((first, last))
        return scheduled

    monkeypatch.setattr(scheduling, "count_scheduled_staff_between", count_scheduled_staff_between)
    monkeypatch.setattr(scheduling, "count_scheduled_staff", not_implemented)
    manager = login(seeded, "manager", ADMIN_PASSWORD)
    days = manager.get(f"/api/forecast?start={start}&days=7").get_json()["days"]

    assert asked == [("2026-12-07", "2026-12-13")]
    for day in days:
        assert day["scheduled_staff"] == scheduled[day["date"]]
        assert day["gap"] == day["predicted_staff_needed"] - day["scheduled_staff"]


def test_forecast_falls_back_to_one_call_per_day(seeded, monkeypatch):
    start = date(2026, 12, 7)
    scheduled = {(start + timedelta(days=n)).isoformat(): n for n in range(7)}
    asked = []

    def count_scheduled_staff(on_date):
        asked.append(on_date)
        return scheduled[on_date]

    monkeypatch.setattr(scheduling, "count_scheduled_staff_between", not_implemented)
    monkeypatch.setattr(scheduling, "count_scheduled_staff", count_scheduled_staff)
    manager = login(seeded, "manager", ADMIN_PASSWORD)
    days = manager.get(f"/api/forecast?start={start}&days=7").get_json()["days"]

    assert asked == list(scheduled)
    for day in days:
        assert day["scheduled_staff"] == scheduled[day["date"]]
        assert day["gap"] == day["predicted_staff_needed"] - day["scheduled_staff"]


def test_model_beats_baseline_on_fixed_history(app, manager):
    with app.app_context():
        save_history(generate_sample_history(end=date(2026, 5, 1)))
    metrics = manager.post("/api/forecast/train").get_json()
    assert metrics["method"] == "random_forest"
    assert metrics["beats_baseline"]
    assert metrics["mae"] < metrics["baseline_mae"]


def test_assigning_a_shift_updates_the_forecast(seeded):
    manager = login(seeded, "manager", ADMIN_PASSWORD)
    today = date.today().isoformat()

    def scheduled_today():
        return manager.get(f"/api/forecast?start={today}&days=1").get_json()["days"][0]

    seeded_shifts = manager.get(f"/api/shifts?start={today}&end={today}").get_json()
    assigned = {s["employee_id"] for s in seeded_shifts if s["status"] == "assigned"}
    before = scheduled_today()
    assert before["scheduled_staff"] == len(assigned)

    newcomer = manager.post("/api/employees", json={"name": "Casey", "position": "Host"})
    weekday = date.today().weekday()
    manager.post(
        f"/api/employees/{newcomer.get_json()['id']}/availability",
        json={"day_of_week": weekday, "start_time": "06:00", "end_time": "22:00"},
    )
    shift = manager.post(
        "/api/shifts", json={"date": today, "start_time": "18:00", "end_time": "21:00"}
    ).get_json()
    res = manager.post(
        f"/api/shifts/{shift['id']}/assign", json={"employee_id": newcomer.get_json()["id"]}
    )
    assert res.status_code == 200, res.get_json()

    after = scheduled_today()
    assert after["scheduled_staff"] == before["scheduled_staff"] + 1
    assert after["gap"] == before["gap"] - 1


def test_approved_replacement_closes_forecast_gap(seeded):
    manager = login(seeded, "manager", ADMIN_PASSWORD)
    day = date.today()
    employee_ids = []

    for name in ("Workflow Alex", "Workflow Sam"):
        created = manager.post("/api/employees", json={"name": name, "position": "Host"})
        assert created.status_code == 201
        employee_id = created.get_json()["id"]
        employee_ids.append(employee_id)

        availability = manager.post(
            f"/api/employees/{employee_id}/availability",
            json={
                "day_of_week": day.weekday(),
                "start_time": "06:00",
                "end_time": "22:00",
            },
        )
        assert availability.status_code == 201

    absent_id, replacement_id = employee_ids
    created_shift = manager.post(
        "/api/shifts",
        json={
            "date": day.isoformat(),
            "start_time": "18:00",
            "end_time": "21:00",
        },
    )
    assert created_shift.status_code == 201
    shift_id = created_shift.get_json()["id"]

    assigned = manager.post(
        f"/api/shifts/{shift_id}/assign",
        json={"employee_id": absent_id},
    )
    assert assigned.status_code == 200

    def forecast_day():
        response = manager.get(f"/api/forecast?start={day.isoformat()}&days=1")
        assert response.status_code == 200
        return response.get_json()["days"][0]

    before = forecast_day()

    absence = manager.post(
        "/api/absences",
        json={"employee_id": absent_id, "date": day.isoformat()},
    )
    assert absence.status_code == 201
    after_absence = forecast_day()
    assert after_absence["scheduled_staff"] == before["scheduled_staff"] - 1
    assert after_absence["gap"] == before["gap"] + 1

    recommendations = manager.get(f"/api/shifts/{shift_id}/recommendations?limit=50")
    assert recommendations.status_code == 200
    candidates = [item["employee_id"] for item in recommendations.get_json()]
    assert replacement_id in candidates
    assert absent_id not in candidates

    after_recommendations = forecast_day()
    assert after_recommendations["scheduled_staff"] == after_absence["scheduled_staff"]

    approved = manager.post(
        f"/api/shifts/{shift_id}/recommendations/approve",
        json={"employee_id": replacement_id},
    )
    assert approved.status_code == 200
    assert approved.get_json()["employee_id"] == replacement_id
    assert approved.get_json()["status"] == "assigned"

    after_approval = forecast_day()
    assert after_approval["scheduled_staff"] == before["scheduled_staff"]
    assert after_approval["gap"] == before["gap"]
    assert after_approval["predicted_staff_needed"] == before["predicted_staff_needed"]
