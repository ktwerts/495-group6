"""Staffing demand model."""

import math
from datetime import date

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from app.forecasting.features import build_features, history_to_xy

MIN_HISTORY_DAYS = 28
TEST_FRACTION = 0.2


def weekday_averages(rows, field: str) -> dict[int, float]:
    values: dict[int, list[float]] = {}
    for row in rows:
        weekday = date.fromisoformat(row["record_date"]).weekday()
        values.setdefault(weekday, []).append(float(row[field]))
    return {weekday: sum(v) / len(v) for weekday, v in values.items()}


def _lookup(averages: dict[int, float], day: date) -> float:
    if day.weekday() in averages:
        return averages[day.weekday()]
    return sum(averages.values()) / len(averages)


class StaffingForecaster:
    def __init__(self, min_history: int = MIN_HISTORY_DAYS, random_state: int = 42):
        if min_history < 2:
            raise ValueError("min_history must be at least 2 to split into train and test")
        self.min_history = min_history
        self.random_state = random_state
        self.model: RandomForestRegressor | None = None
        self.staff_by_weekday: dict[int, float] = {}
        self.workload_by_weekday: dict[int, float] = {}
        self.metrics: dict = {}

    @property
    def method(self) -> str:
        return "random_forest" if self.model is not None else "weekday_average"

    def _new_model(self) -> RandomForestRegressor:
        return RandomForestRegressor(
            n_estimators=100, min_samples_leaf=2, random_state=self.random_state
        )

    def train(self, rows) -> dict:
        rows = sorted(rows, key=lambda r: r["record_date"])
        if not rows:
            raise ValueError("no staffing history to train on")

        # Build everything first so a failed retrain leaves the previous model in place.
        model, metrics = self._fit(rows) if len(rows) >= self.min_history else (None, None)
        self.model = model
        self.staff_by_weekday = weekday_averages(rows, "staff_needed")
        self.workload_by_weekday = weekday_averages(rows, "workload_units")
        self.metrics = metrics or {"method": "weekday_average", "history_days": len(rows)}
        return self.metrics

    def _fit(self, rows) -> tuple[RandomForestRegressor, dict]:
        # Hold out the most recent days so the evaluation never trains on the future.
        split = int(len(rows) * (1 - TEST_FRACTION))
        train_rows, test_rows = rows[:split], rows[split:]
        x_train, y_train = history_to_xy(train_rows)
        x_test, y_test = history_to_xy(test_rows)

        evaluation_model = self._new_model()
        evaluation_model.fit(x_train, y_train)
        mae = mean_absolute_error(y_test, evaluation_model.predict(x_test))

        baseline = weekday_averages(train_rows, "staff_needed")
        baseline_predictions = [
            _lookup(baseline, date.fromisoformat(r["record_date"])) for r in test_rows
        ]
        baseline_mae = mean_absolute_error(y_test, baseline_predictions)

        model = self._new_model()
        model.fit(*history_to_xy(rows))
        return model, {
            "method": "random_forest",
            "history_days": len(rows),
            "test_days": len(test_rows),
            "test_from": test_rows[0]["record_date"],
            "mae": round(float(mae), 3),
            "baseline_mae": round(float(baseline_mae), 3),
            "beats_baseline": bool(mae < baseline_mae),
        }

    def expected_workload(self, day: date) -> float:
        self._require_trained()
        return _lookup(self.workload_by_weekday, day)

    def predict(self, day: date, workload_units: float | None = None) -> int:
        self._require_trained()
        if self.model is None:
            raw = _lookup(self.staff_by_weekday, day)
        else:
            if workload_units is None:
                workload_units = self.expected_workload(day)
            raw = float(self.model.predict([build_features(day, workload_units)])[0])
        # Round up: being one person short hurts more than one extra.
        return max(1, math.ceil(round(raw, 6)))

    def _require_trained(self) -> None:
        if not self.staff_by_weekday:
            raise RuntimeError("model has not been trained")
