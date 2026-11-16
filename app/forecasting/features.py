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
    if workload_units < 0:
        raise ValueError("workload_units cannot be negative")
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
    features, targets = [], []
    for row in rows:
        day = date.fromisoformat(row["record_date"])
        features.append(build_features(day, row["workload_units"]))
        targets.append(int(row["staff_needed"]))
    return features, targets
