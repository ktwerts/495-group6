"""Performance benchmarks with minimum acceptable thresholds.

The assignment's professional standards ask for performance benchmarks. Keep the
limits generous so they pass on slow CI runners but still catch regressions, such
as retraining the model on every request or running a query inside a loop.
"""

import time

from app.db import get_db
from app.forecasting.history import seed_staffing_history
from app.scheduling import service as scheduling

HEALTH_LIMIT_SECONDS = 0.5
RECOMMEND_LIMIT_SECONDS = 1.0
FORECAST_LIMIT_SECONDS = 1.0
TRAIN_LIMIT_SECONDS = 10.0


def timed(fn):
    start = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - start


def test_health_check_is_fast(client):
    """Working example of the pattern."""
    res, seconds = timed(lambda: client.get("/health"))
    assert res.status_code == 200
    assert seconds < HEALTH_LIMIT_SECONDS


def test_recommendations_scale_to_many_employees(app, manager):
    with app.app_context():
        db = get_db()
        for number in range(50):
            employee_id = db.execute(
                """
                INSERT INTO employees
                    (name, position, qualifications, max_weekly_hours)
                VALUES (?, ?, ?, ?)
                """,
                (f"Employee {number}", "Cook", '["food safety"]', 40),
            ).lastrowid
            db.execute(
                """
                INSERT INTO availability
                    (employee_id, day_of_week, start_time, end_time)
                VALUES (?, ?, ?, ?)
                """,
                (employee_id, 1, "09:00", "17:00"),
            )
        db.commit()

    created = manager.post(
        "/api/shifts",
        json={
            "date": "2026-11-17",
            "start_time": "09:00",
            "end_time": "13:00",
            "required_qualification": "food safety",
        },
    )
    assert created.status_code == 201
    shift_id = created.get_json()["id"]

    response, seconds = timed(
        lambda: manager.get(f"/api/shifts/{shift_id}/recommendations?limit=50")
    )

    assert response.status_code == 200
    candidates = response.get_json()
    assert len(candidates) == 50
    assert len({candidate["employee_id"] for candidate in candidates}) == 50
    assert seconds < RECOMMEND_LIMIT_SECONDS


def test_forecast_month_is_fast_once_trained(app, manager, monkeypatch):
    with app.app_context():
        seed_staffing_history(days=365)
    monkeypatch.setattr(scheduling, "count_scheduled_staff", lambda on_date: 3)

    res, train_seconds = timed(lambda: manager.post("/api/forecast/train"))
    assert res.status_code == 200
    assert train_seconds < TRAIN_LIMIT_SECONDS

    res, seconds = timed(lambda: manager.get("/api/forecast?days=31"))
    assert res.status_code == 200
    assert len(res.get_json()["days"]) == 31
    assert seconds < FORECAST_LIMIT_SECONDS
