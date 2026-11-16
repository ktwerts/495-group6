"""Forecasting (AI) module tests. Owner: Integration Lead.

These are templates: remove the skip marker as you implement each feature.
Test the model on small synthetic data so tests stay fast and deterministic
(set random_state).
"""

import math
from datetime import date, timedelta

import pytest

from app.forecasting.features import FEATURE_NAMES, build_features, history_to_xy

TODO = pytest.mark.skip(reason="TODO: implement forecasting module")

FRIDAY = date(2026, 1, 9)


def test_build_features_shape():
    for offset in range(14):
        features = build_features(FRIDAY + timedelta(days=offset), 50)
        assert len(features) == len(FEATURE_NAMES)
        assert all(isinstance(value, float) for value in features)


def named(day, workload=50.0):
    return dict(zip(FEATURE_NAMES, build_features(day, workload), strict=True))


def test_day_flags():
    friday, saturday, sunday, monday = (named(FRIDAY + timedelta(days=n)) for n in range(4))
    assert (friday["is_friday"], friday["is_weekend"]) == (1.0, 0.0)
    assert saturday["is_weekend"] == sunday["is_weekend"] == 1.0
    assert (monday["is_friday"], monday["is_weekend"], monday["day_of_week"]) == (0.0, 0.0, 0.0)


def test_season_wraps_around_new_year():
    dec_31 = named(date(2025, 12, 31))
    jan_1 = named(date(2026, 1, 1))
    jul_1 = named(date(2026, 7, 1))

    def distance(a, b):
        return math.dist((a["season_sin"], a["season_cos"]), (b["season_sin"], b["season_cos"]))

    assert distance(dec_31, jan_1) < 0.05
    assert distance(jan_1, jul_1) > 1.9


def test_workload_passes_through():
    assert named(FRIDAY, 72.5)["workload_units"] == 72.5


def test_negative_workload_rejected():
    with pytest.raises(ValueError):
        build_features(FRIDAY, -1)


def test_history_to_xy():
    rows = [
        {"record_date": "2026-01-09", "workload_units": 70.0, "staff_needed": 5, "absences": 1},
        {"record_date": "2026-01-10", "workload_units": 90.0, "staff_needed": 6, "absences": 0},
    ]
    features, targets = history_to_xy(rows)
    assert targets == [5, 6]
    assert features == [build_features(FRIDAY, 70.0), build_features(FRIDAY + timedelta(1), 90.0)]


def test_history_to_xy_empty():
    assert history_to_xy([]) == ([], [])


@TODO
def test_model_trains_and_reports_metrics():
    """train() on synthetic history returns an error metric (e.g. MAE) and a baseline to compare."""


@TODO
def test_predictions_are_positive_integers():
    """predict() never returns 0 or negative staff."""


@TODO
def test_not_enough_history_is_handled():
    """With little or no history, the service falls back or returns a clear 400, not a crash."""


@TODO
def test_forecast_endpoint_shows_gap(manager):
    """Integration: /api/forecast compares predictions with scheduling.count_scheduled_staff()."""
