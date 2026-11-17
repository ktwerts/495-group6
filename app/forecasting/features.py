"""Turns staffing history into model inputs."""

import math
from datetime import date

FEATURE_NAMES = [
    "day_of_week",
    "is_friday",
    "is_weekend",
    "month",
    "season_sin",
    "season_cos",
    "workload_units",
]


def build_features(day: date, workload_units: float) -> list[float]:
    """Return the values for one day, in FEATURE_NAMES order.

    workload_units must be a finite number >= 0.
    """
    if not math.isfinite(workload_units) or workload_units < 0:
        raise ValueError(f"workload_units must be a finite number >= 0, got {workload_units!r}")
    weekday = day.weekday()
    # sin/cos keeps Dec 31 and Jan 1 close together instead of 365 apart
    angle = 2 * math.pi * day.timetuple().tm_yday / 365.25
    return [
        float(weekday),
        1.0 if weekday == 4 else 0.0,
        1.0 if weekday >= 5 else 0.0,
        float(day.month),
        math.sin(angle),
        math.cos(angle),
        float(workload_units),
    ]


def history_to_xy(rows) -> tuple[list[list[float]], list[int]]:
    """Split staffing-history rows into features (X) and staff_needed targets (y).

    Each row needs record_date (YYYY-MM-DD), workload_units and staff_needed,
    where staff_needed is a whole number >= 1.
    """
    features, targets = [], []
    for row in rows:
        day = date.fromisoformat(row["record_date"])
        features.append(build_features(day, row["workload_units"]))
        targets.append(_staff_count(row["staff_needed"], row["record_date"]))
    return features, targets


def _staff_count(value, record_date: str) -> int:
    whole = isinstance(value, int) or (isinstance(value, float) and value.is_integer())
    if isinstance(value, bool) or not whole or value < 1:
        raise ValueError(
            f"staff_needed on {record_date} must be a whole number >= 1, got {value!r}"
        )
    return int(value)
