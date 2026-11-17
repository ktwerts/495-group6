"""Forecasting (AI) module tests. Owner: Integration Lead.

These are templates: remove the skip marker as you implement each feature.
Test the model on small synthetic data so tests stay fast and deterministic
(set random_state).
"""

import math
import random
from datetime import date, timedelta

import pytest

from app.forecasting.features import FEATURE_NAMES, build_features, history_to_xy
from app.forecasting.model import StaffingForecaster

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


@pytest.mark.parametrize("workload", [-1, float("nan"), float("inf"), float("-inf")])
def test_invalid_workload_rejected(workload):
    with pytest.raises(ValueError):
        build_features(FRIDAY, workload)


@pytest.mark.parametrize("workload", [0, 0.0, 42.75])
def test_zero_and_decimal_workload_allowed(workload):
    assert named(FRIDAY, workload)["workload_units"] == workload


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


def history_row(staff_needed):
    return {"record_date": "2026-01-09", "workload_units": 50.0, "staff_needed": staff_needed}


@pytest.mark.parametrize("staff_needed", [3, 3.0])
def test_whole_staff_count_accepted(staff_needed):
    _, targets = history_to_xy([history_row(staff_needed)])
    assert targets == [3] and isinstance(targets[0], int)


@pytest.mark.parametrize("staff_needed", [3.9, 0, -2, float("nan"), True, "3"])
def test_invalid_staff_count_rejected(staff_needed):
    with pytest.raises(ValueError, match="2026-01-09"):
        history_to_xy([history_row(staff_needed)])


def sample_rows(days=120, start=date(2026, 1, 5), seed=0):
    rng = random.Random(seed)  # noqa: S311
    rows = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        workload = rng.uniform(40, 70) + (30 if day.weekday() >= 5 else 0)
        rows.append(
            {
                "record_date": day.isoformat(),
                "workload_units": round(workload, 1),
                "staff_needed": math.ceil(workload / 15),
            }
        )
    return rows


@pytest.fixture(scope="module")
def trained():
    forecaster = StaffingForecaster()
    forecaster.train(sample_rows())
    return forecaster


def test_model_trains_and_reports_metrics(trained):
    metrics = trained.metrics
    assert trained.method == "random_forest"
    assert metrics["history_days"] == 120
    assert metrics["test_days"] == 24
    assert metrics["mae"] >= 0 and metrics["baseline_mae"] >= 0


def test_evaluation_holds_out_most_recent_days():
    rows = sample_rows()
    metrics = StaffingForecaster().train(list(reversed(rows)))
    assert metrics["test_from"] == rows[96]["record_date"]


def test_model_beats_weekday_baseline_when_workload_varies(trained):
    assert trained.metrics["beats_baseline"] is True
    assert trained.metrics["mae"] < trained.metrics["baseline_mae"]


def test_predictions_are_positive_integers(trained):
    for offset in range(14):
        prediction = trained.predict(date(2026, 6, 1) + timedelta(days=offset))
        assert isinstance(prediction, int) and prediction >= 1
    assert trained.predict(date(2026, 6, 1), workload_units=0) >= 1


def test_predictions_follow_patterns(trained):
    wednesday, saturday = date(2026, 6, 3), date(2026, 6, 6)
    assert trained.predict(saturday) > trained.predict(wednesday)
    assert trained.predict(wednesday, workload_units=90) > trained.predict(
        wednesday, workload_units=30
    )


def test_training_is_deterministic():
    first, second = StaffingForecaster(), StaffingForecaster()
    assert first.train(sample_rows()) == second.train(sample_rows())
    day = date(2026, 6, 6)
    assert first.predict(day) == second.predict(day)


def test_not_enough_history_falls_back_to_weekday_average():
    rows = sample_rows(days=10)
    forecaster = StaffingForecaster()
    metrics = forecaster.train(rows)
    assert forecaster.method == "weekday_average"
    assert metrics == {"method": "weekday_average", "history_days": 10}

    monday_staff = [
        r["staff_needed"] for r in rows if r["record_date"] in ("2026-01-05", "2026-01-12")
    ]
    assert forecaster.predict(date(2026, 6, 1)) == math.ceil(sum(monday_staff) / 2)


def test_fallback_handles_weekday_missing_from_history():
    forecaster = StaffingForecaster()
    forecaster.train(sample_rows(days=3))
    assert forecaster.predict(date(2026, 6, 5)) >= 1


def test_empty_history_rejected():
    with pytest.raises(ValueError):
        StaffingForecaster().train([])


def test_failed_retrain_keeps_previous_model():
    forecaster = StaffingForecaster()
    metrics = forecaster.train(sample_rows())
    before = forecaster.predict(date(2026, 6, 6))

    bad_rows = sample_rows()
    bad_rows[50]["workload_units"] = -5
    with pytest.raises(ValueError):
        forecaster.train(bad_rows)

    assert forecaster.method == "random_forest"
    assert forecaster.metrics == metrics
    assert forecaster.predict(date(2026, 6, 6)) == before


def test_min_history_must_allow_a_train_test_split():
    with pytest.raises(ValueError):
        StaffingForecaster(min_history=1)
    assert StaffingForecaster(min_history=2).train(sample_rows(days=2))["method"] == "random_forest"


def test_predict_before_training_rejected():
    with pytest.raises(RuntimeError):
        StaffingForecaster().predict(date(2026, 6, 1))


@TODO
def test_forecast_endpoint_shows_gap(manager):
    """Integration: /api/forecast compares predictions with scheduling.count_scheduled_staff()."""
