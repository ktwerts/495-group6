import sqlite3
from datetime import date, timedelta
from statistics import mean

import pytest

from app.db import get_db
from app.forecasting.history import (
    DEFAULT_DAYS,
    generate_sample_history,
    load_history,
    save_history,
)

END = date(2026, 6, 30)


def row(record_date="2026-01-05", workload=60.0, staff=4, absences=0):
    return {
        "record_date": record_date,
        "workload_units": workload,
        "staff_needed": staff,
        "absences": absences,
    }


def test_generates_consecutive_days_ending_on_end_date():
    rows = generate_sample_history(days=30, end=END)
    dates = [date.fromisoformat(r["record_date"]) for r in rows]
    assert len(rows) == 30
    assert dates[-1] == END
    assert all(b - a == timedelta(days=1) for a, b in zip(dates, dates[1:], strict=False))


def test_defaults_to_ending_yesterday():
    rows = generate_sample_history(days=3)
    assert rows[-1]["record_date"] == (date.today() - timedelta(days=1)).isoformat()


def test_same_seed_gives_same_data():
    assert generate_sample_history(end=END) == generate_sample_history(end=END)
    assert generate_sample_history(end=END) != generate_sample_history(end=END, seed=7)


def test_values_are_valid():
    for r in generate_sample_history(end=END):
        assert r["workload_units"] >= 10
        assert r["staff_needed"] >= 1
        assert r["absences"] >= 0


def test_weekends_are_busier_than_weekdays():
    rows = generate_sample_history(end=END)
    weekend = [r for r in rows if date.fromisoformat(r["record_date"]).weekday() >= 5]
    weekday = [r for r in rows if r not in weekend]
    assert mean(r["workload_units"] for r in weekend) > mean(r["workload_units"] for r in weekday)
    assert mean(r["staff_needed"] for r in weekend) > mean(r["staff_needed"] for r in weekday)


def test_rejects_non_positive_days():
    with pytest.raises(ValueError):
        generate_sample_history(days=0)


def test_save_and_load_round_trip_oldest_first(app):
    rows = generate_sample_history(days=10, end=END)
    with app.app_context():
        assert save_history(list(reversed(rows))) == 10
        assert load_history() == rows


@pytest.mark.parametrize("bad_row", [row(staff=0), row(workload=-1), row(absences=-2)])
def test_table_rejects_invalid_values(app, bad_row):
    with app.app_context(), pytest.raises(sqlite3.IntegrityError):
        save_history([bad_row])


def test_duplicate_date_rolls_back_whole_batch(app):
    with app.app_context():
        save_history([row("2026-01-05")])
        with pytest.raises(sqlite3.IntegrityError):
            save_history([row("2026-01-06"), row("2026-01-05")])
        assert [r["record_date"] for r in load_history()] == ["2026-01-05"]


def test_flask_seed_loads_history(app, monkeypatch):
    monkeypatch.setenv("SHIFTWISE_ADMIN_PASSWORD", "demo-password-1")
    result = app.test_cli_runner().invoke(args=["seed"])
    assert result.exit_code == 0, result.output
    with app.app_context():
        count = get_db().execute("SELECT COUNT(*) FROM staffing_history").fetchone()[0]
    assert count == DEFAULT_DAYS
