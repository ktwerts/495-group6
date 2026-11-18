"""Scheduling module tests. Owner: Lead Architect.

The constraint functions are pure, so test them directly without the database.
"""

import pytest

from app.scheduling import constraints

SHIFT = {
    "date": "2026-11-17",
    "start_time": "09:00",
    "end_time": "17:00",
    "required_qualification": "Cashier",
}


def test_shift_routes_are_manager_only(client, staff):
    assert staff.get("/api/shifts").status_code == 403
    assert staff.post("/api/shifts", json=SHIFT).status_code == 403
    staff.post("/api/auth/logout")
    assert client.get("/api/shifts").status_code == 401
    assert client.post("/api/shifts", json=SHIFT).status_code == 401


def test_create_shift_requires_json_object(manager):
    assert manager.post("/api/shifts", json=["not", "an", "object"]).status_code == 400


def test_list_shifts_filters_by_date(manager):
    for day in ("2026-11-16", "2026-11-17", "2026-11-18"):
        assert manager.post("/api/shifts", json={**SHIFT, "date": day}).status_code == 201

    res = manager.get("/api/shifts?start=2026-11-17&end=2026-11-18")
    assert [shift["date"] for shift in res.get_json()] == ["2026-11-17", "2026-11-18"]
    assert manager.get("/api/shifts?start=2026-11-18&end=2026-11-17").status_code == 400
    assert manager.get("/api/shifts?start=11/17/2026").status_code == 400


TODO = pytest.mark.skip(reason="TODO: implement scheduling module")


def test_times_overlap():
    assert constraints.times_overlap("09:00", "12:00", "11:00", "13:00")
    assert not constraints.times_overlap("09:00", "12:00", "12:00", "15:00")


def test_check_assignment_detects_missing_qualification():
    """Check that an employee has the required qualification."""

    employee = {"active": True, "qualifications": ["Cashier"]}

    shift = {
        "date": "2026-11-17",
        "start_time": "09:00",
        "end_time": "17:00",
        "required_qualification": "Manager",
    }

    availability = [{"day_of_week": 1, "start_time": "08:00", "end_time": "18:00"}]

    violations = constraints.check_assignment(employee, shift, availability=availability)

    assert "Employee does not have the required qualification." in violations


def test_create_shift_rejects_end_before_start():
    """Reject shifts that end before they start."""
    from app.errors import ValidationError
    from app.scheduling.service import create_shift

    shift = {
        "date": "2026-11-17",
        "start_time": "17:00",
        "end_time": "09:00",
        "required_qualification": "Cashier",
    }

    with pytest.raises(ValidationError):
        create_shift(shift)


def test_create_shift_normalizes_single_digit_hour(app):
    """Store single-digit hours in HH:MM format."""
    from app.scheduling.service import create_shift

    with app.app_context():
        shift = create_shift(
            {
                "date": "2026-11-17",
                "start_time": "9:00",
                "end_time": "17:00",
                "required_qualification": "Cashier",
            }
        )

    assert shift["start_time"] == "09:00"
    assert shift["end_time"] == "17:00"
    assert shift["status"] == "open"


def test_count_scheduled_staff_counts_assigned_employees(app):
    """Count distinct assigned employees, excluding open and cancelled shifts."""
    from app.db import get_db
    from app.scheduling.service import count_scheduled_staff

    with app.app_context():
        db = get_db()

        db.executemany(
            """
            INSERT INTO shifts
            (date, start_time, end_time, required_qualification, employee_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("2026-11-17", "09:00", "12:00", "Cashier", 1, "assigned"),
                ("2026-11-17", "13:00", "17:00", "Cashier", 1, "assigned"),
                ("2026-11-17", "09:00", "12:00", "Cashier", 2, "assigned"),
                ("2026-11-17", "09:00", "12:00", "Cashier", None, "open"),
                ("2026-11-17", "09:00", "12:00", "Cashier", 3, "cancelled"),
            ],
        )
        db.commit()

        assert count_scheduled_staff("2026-11-17") == 2


def test_single_digit_time_overlap():
    """A single-digit start hour should not bypass overlap detection."""
    assert constraints.times_overlap("9:00", "9:30", "09:15", "09:45")


@TODO
def test_conflicting_assignment_returns_409(manager):
    """Assign the same employee to overlapping shifts and expect 409."""


@TODO
def test_absence_opens_shift_and_recommendations_exclude_absent(manager):
    """Report absence, reopen shift, and exclude absent employee."""
