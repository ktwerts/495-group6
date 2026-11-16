"""Staffing history used to train the forecast model."""

import math
import random
from datetime import date, timedelta

from app.db import get_db

DEFAULT_DAYS = 180

BASE_WORKLOAD = 60.0
FRIDAY_BOOST = 10.0
WEEKEND_BOOST = 25.0
SEASONAL_AMPLITUDE = 8.0
WORKLOAD_NOISE = 6.0
WORKLOAD_PER_STAFF = 15.0
STAFFING_NOISE = 0.5
MEAN_ABSENCES = 0.8


def generate_sample_history(
    days: int = DEFAULT_DAYS, end: date | None = None, seed: int = 42
) -> list[dict]:
    """Synthetic daily history ending on `end` (defaults to yesterday). See TD-3."""
    if days < 1:
        raise ValueError("days must be at least 1")
    rng = random.Random(seed)  # noqa: S311
    end = end or date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)

    rows = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        workload = BASE_WORKLOAD
        if day.weekday() == 4:
            workload += FRIDAY_BOOST
        elif day.weekday() >= 5:
            workload += WEEKEND_BOOST
        workload += SEASONAL_AMPLITUDE * math.sin(2 * math.pi * day.timetuple().tm_yday / 365)
        workload = max(10.0, workload + rng.gauss(0, WORKLOAD_NOISE))

        staff_needed = round(workload / WORKLOAD_PER_STAFF + rng.gauss(0, STAFFING_NOISE))
        rows.append(
            {
                "record_date": day.isoformat(),
                "workload_units": round(workload, 1),
                "staff_needed": max(1, staff_needed),
                "absences": max(0, round(rng.gauss(MEAN_ABSENCES, MEAN_ABSENCES))),
            }
        )
    return rows


def save_history(rows: list[dict]) -> int:
    db = get_db()
    with db:
        db.executemany(
            "INSERT INTO staffing_history (record_date, workload_units, staff_needed, absences)"
            " VALUES (:record_date, :workload_units, :staff_needed, :absences)",
            rows,
        )
    return len(rows)


def load_history() -> list[dict]:
    rows = get_db().execute(
        "SELECT record_date, workload_units, staff_needed, absences"
        " FROM staffing_history ORDER BY record_date"
    )
    return [dict(row) for row in rows]


def seed_staffing_history(days: int = DEFAULT_DAYS) -> int:
    return save_history(generate_sample_history(days))
