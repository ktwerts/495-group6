"""Performance benchmarks with minimum acceptable thresholds.

The assignment's professional standards ask for performance benchmarks. Keep the
limits generous so they pass on slow CI runners but still catch regressions, such
as retraining the model on every request or running a query inside a loop.
"""

import time

import pytest

from app.forecasting.history import seed_staffing_history
from app.scheduling import service as scheduling

TODO = pytest.mark.skip(reason="TODO: enable once the feature exists")

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


@TODO
def test_recommendations_scale_to_many_employees(manager):
    """Owner: Lead Architect. Create ~50 employees, then time ranking replacements."""


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
