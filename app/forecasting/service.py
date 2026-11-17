"""Connects the staffing model to the database and the schedule."""

import os
from datetime import date, timedelta

import joblib
from flask import current_app

from app.db import get_db
from app.errors import ValidationError
from app.forecasting.history import load_history
from app.forecasting.model import StaffingForecaster
from app.scheduling import service as scheduling

CACHE_KEY = "staffing_forecaster"


def _history_version() -> tuple[int, str | None]:
    row = get_db().execute("SELECT COUNT(*), MAX(record_date) FROM staffing_history").fetchone()
    return row[0], row[1]


def train_model() -> dict:
    """Train on all staffing history, save the model to MODEL_PATH, and return its metrics."""
    history = load_history()
    if not history:
        raise ValidationError("No staffing history yet. Run `flask seed` to load sample data.")

    forecaster = StaffingForecaster()
    try:
        metrics = forecaster.train(history)
    except ValueError as exc:
        raise ValidationError(f"Staffing history has invalid data: {exc}") from exc

    version = _history_version()
    joblib.dump({"forecaster": forecaster, "history_version": version}, _model_path())
    current_app.extensions[CACHE_KEY] = (forecaster, version)
    return metrics


def get_forecaster() -> StaffingForecaster:
    """Return a model trained on the current history, retraining only when needed."""
    version = _history_version()
    cached = current_app.extensions.get(CACHE_KEY) or _load_saved_model()
    if cached and cached[1] == version:
        current_app.extensions[CACHE_KEY] = cached
        return cached[0]
    train_model()
    return current_app.extensions[CACHE_KEY][0]


def _load_saved_model() -> tuple[StaffingForecaster, tuple] | None:
    path = _model_path()
    if not os.path.exists(path):
        return None
    try:
        # joblib uses pickle, so only the file this app writes to instance/ is ever loaded (TD-6)
        saved = joblib.load(path)
        if not isinstance(saved.get("forecaster"), StaffingForecaster):
            raise TypeError("unexpected contents")
        return saved["forecaster"], tuple(saved["history_version"])
    except Exception:
        current_app.logger.warning("Ignoring unreadable model file %s; retraining", path)
        return None


def _model_path() -> str:
    return current_app.config["MODEL_PATH"]


def _scheduled_staff(day: date) -> int | None:
    try:
        return scheduling.count_scheduled_staff(day.isoformat())
    except NotImplementedError:
        return None


def forecast(start: date, days: int) -> dict:
    """Predicted vs. scheduled staff for each day from `start`.

    gap is predicted minus scheduled (positive means understaffed). scheduled_staff and
    gap are None while the scheduling module can't report counts.
    """
    forecaster = get_forecaster()
    results = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        predicted = forecaster.predict(day)
        scheduled = _scheduled_staff(day)
        results.append(
            {
                "date": day.isoformat(),
                "expected_workload": round(forecaster.expected_workload(day), 1),
                "predicted_staff_needed": predicted,
                "scheduled_staff": scheduled,
                "gap": None if scheduled is None else predicted - scheduled,
            }
        )
    return {"method": forecaster.method, "metrics": forecaster.metrics, "days": results}
