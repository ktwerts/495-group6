"""Connects the staffing model to the database and the schedule."""

import os
import tempfile
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

    forecaster = StaffingForecaster(min_history=current_app.config["FORECAST_MIN_HISTORY"])
    try:
        metrics = forecaster.train(history)
    except ValueError as exc:
        raise ValidationError(f"Staffing history has invalid data: {exc}") from exc

    version = _history_version()
    _save_model({"forecaster": forecaster, "history_version": version})
    current_app.extensions[CACHE_KEY] = (forecaster, version)
    return metrics


def _save_model(contents: dict) -> None:
    # Write to a temp file and swap it in, so a crash or a second retrain never leaves half a file
    path = _model_path()
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
    os.close(fd)
    try:
        joblib.dump(contents, tmp_path)
        os.replace(tmp_path, path)
    except BaseException:
        os.remove(tmp_path)
        raise


def get_forecaster() -> StaffingForecaster:
    """Return a model trained on the current history and settings, retraining only when needed."""
    version = _history_version()
    cached = current_app.extensions.get(CACHE_KEY) or _load_saved_model()
    min_history = current_app.config["FORECAST_MIN_HISTORY"]
    if cached and cached[1] == version and cached[0].min_history == min_history:
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


def _scheduled_counts(dates: list[str]) -> list[int | None]:
    try:
        counts = scheduling.count_scheduled_staff_between(dates[0], dates[-1])
        return [counts.get(day, 0) for day in dates]
    except NotImplementedError:
        pass
    try:
        return [scheduling.count_scheduled_staff(day) for day in dates]
    except NotImplementedError:
        return [None] * len(dates)


def forecast(start: date, days: int) -> dict:
    """Predicted vs. scheduled staff for each day from `start`.

    gap is predicted minus scheduled (positive means understaffed). scheduled_staff and
    gap are None while the scheduling module can't report counts.
    """
    forecaster = get_forecaster()
    dates = [start + timedelta(days=offset) for offset in range(days)]
    scheduled_counts = _scheduled_counts([day.isoformat() for day in dates])
    results = []
    for day, scheduled in zip(dates, scheduled_counts, strict=True):
        predicted = forecaster.predict(day)
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
