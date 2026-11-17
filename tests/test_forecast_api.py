import os
import re
from datetime import date, timedelta

import joblib
import pytest

from app.db import get_db
from app.forecasting import service
from app.forecasting.history import save_history, seed_staffing_history
from app.scheduling import service as scheduling


@pytest.fixture
def history(app):
    with app.app_context():
        seed_staffing_history()


@pytest.fixture
def scheduled(monkeypatch):
    monkeypatch.setattr(scheduling, "count_scheduled_staff", lambda on_date: 2)


def forget_cached_model(app):
    app.extensions.pop(service.CACHE_KEY, None)


def test_train_returns_metrics_and_saves_model(app, manager, history):
    res = manager.post("/api/forecast/train")
    assert res.status_code == 200
    metrics = res.get_json()
    assert metrics["method"] == "random_forest"
    assert metrics["history_days"] == 180
    assert {"mae", "baseline_mae", "beats_baseline"} <= metrics.keys()
    assert os.path.exists(app.config["MODEL_PATH"])


def test_train_without_history_returns_400(manager):
    res = manager.post("/api/forecast/train")
    assert res.status_code == 400
    assert "flask seed" in res.get_json()["error"]


def test_train_with_invalid_history_returns_400(app, manager, history):
    with app.app_context():
        db = get_db()
        db.execute("UPDATE staffing_history SET staff_needed = 3.9 WHERE rowid = 1")
        db.commit()
    res = manager.post("/api/forecast/train")
    assert res.status_code == 400
    assert "invalid data" in res.get_json()["error"]


def test_forecast_compares_predicted_with_scheduled(manager, history, scheduled):
    res = manager.get("/api/forecast?start=2026-12-07&days=7")
    assert res.status_code == 200
    body = res.get_json()
    assert body["method"] == "random_forest"
    assert [d["date"] for d in body["days"]] == [
        (date(2026, 12, 7) + timedelta(days=n)).isoformat() for n in range(7)
    ]
    for day in body["days"]:
        assert day["predicted_staff_needed"] >= 1
        assert day["scheduled_staff"] == 2
        assert day["gap"] == day["predicted_staff_needed"] - 2


def test_forecast_defaults_to_seven_days_from_today(manager, history, scheduled):
    days = manager.get("/api/forecast").get_json()["days"]
    assert len(days) == 7
    assert days[0]["date"] == date.today().isoformat()


def test_forecast_without_scheduling_leaves_gap_empty(manager, history):
    day = manager.get("/api/forecast?days=1").get_json()["days"][0]
    if day["scheduled_staff"] is not None:
        pytest.skip("scheduling.count_scheduled_staff is implemented now")
    assert day["gap"] is None
    assert day["predicted_staff_needed"] >= 1


@pytest.mark.parametrize("query", ["days=0", "days=32", "days=abc", "start=12/07/2026"])
def test_forecast_rejects_bad_query(manager, history, query):
    assert manager.get(f"/api/forecast?{query}").status_code == 400


def test_forecast_without_history_returns_400(manager):
    assert manager.get("/api/forecast").status_code == 400


def test_forecast_endpoints_are_manager_only(client, staff):
    assert staff.get("/api/forecast").status_code == 403
    assert staff.post("/api/forecast/train").status_code == 403
    staff.post("/api/auth/logout")
    assert client.get("/api/forecast").status_code == 401
    assert client.post("/api/forecast/train").status_code == 401


def test_forecast_trains_automatically_the_first_time(app, manager, history, scheduled):
    assert manager.get("/api/forecast?days=1").status_code == 200
    assert os.path.exists(app.config["MODEL_PATH"])


def test_saved_model_is_reused_after_restart(app, manager, history, scheduled, monkeypatch):
    manager.post("/api/forecast/train")
    forget_cached_model(app)
    monkeypatch.setattr(service, "train_model", lambda: pytest.fail("should not retrain"))
    assert manager.get("/api/forecast?days=1").status_code == 200


def test_new_history_triggers_retraining(app, manager, history, scheduled):
    manager.post("/api/forecast/train")
    with app.app_context():
        save_history(
            [
                {
                    "record_date": date.today().isoformat(),
                    "workload_units": 60.0,
                    "staff_needed": 4,
                    "absences": 0,
                }
            ]
        )
    metrics = manager.get("/api/forecast?days=1").get_json()["metrics"]
    assert metrics["history_days"] == 181


@pytest.mark.parametrize("contents", [b"not a model", None])
def test_unreadable_model_file_is_replaced(app, manager, history, scheduled, contents):
    path = app.config["MODEL_PATH"]
    if contents is None:
        joblib.dump({"forecaster": "something else", "history_version": (180, None)}, path)
    else:
        with open(path, "wb") as f:
            f.write(contents)
    res = manager.get("/api/forecast?days=1")
    assert res.status_code == 200
    assert res.get_json()["method"] == "random_forest"


def test_forecast_page_has_controls(manager):
    html = manager.get("/forecast").get_data(as_text=True)
    for element_id in ("forecast-form", "retrain-btn", "model-summary", "forecast-table"):
        assert f'id="{element_id}"' in html


@pytest.mark.parametrize(
    ("max_days", "options"), [(31, ["7", "14", "31"]), (10, ["7", "10"]), (5, ["5"])]
)
def test_forecast_page_day_options_follow_max_days(app, manager, max_days, options):
    app.config["FORECAST_MAX_DAYS"] = max_days
    html = manager.get("/forecast").get_data(as_text=True)
    assert re.findall(r'<option value="(\d+)">', html) == options


def test_forecast_page_is_manager_only(client, staff):
    assert staff.get("/forecast").status_code == 403
    staff.post("/api/auth/logout")
    assert client.get("/forecast").status_code == 302
