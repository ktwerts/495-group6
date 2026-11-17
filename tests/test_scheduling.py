"""Scheduling module tests. Owner: Lead Architect.

These are templates: remove the skip marker as you implement each feature.
The constraint functions are pure, so test them directly without the database.
"""

import pytest

from app.scheduling import constraints

TODO = pytest.mark.skip(reason="TODO: implement scheduling module")



def test_times_overlap():
    assert constraints.times_overlap("09:00", "12:00", "11:00", "13:00")
    assert not constraints.times_overlap("09:00", "12:00", "12:00", "15:00")



def test_check_assignment_detects_missing_qualification():
    """Check that an employee has the required qualification."""

    employee = {
        "active": True,
        "qualifications": ["Cashier"]
    }

    shift = {
        "date": "2026-11-17",
        "start_time": "09:00",
        "end_time": "17:00",
        "required_qualification": "Manager"
    }

    availability = [
        {
            "day_of_week": 1,
            "start_time": "08:00",
            "end_time": "18:00"
        }
    ]

    violations = constraints.check_assignment(
        employee,
        shift,
        availability=availability
    )

    assert "Employee does not have the required qualification." in violations

def test_create_shift_rejects_end_before_start():
    """Reject shifts that end before they start."""
    from app.errors import ValidationError
    from app.scheduling.service import create_shift

    shift = {
        "date": "2026-11-17",
        "start_time": "17:00",
        "end_time": "09:00",
        "required_qualification": "Cashier"
    }

    with pytest.raises(ValidationError):
        create_shift(shift)


@TODO
def test_conflicting_assignment_returns_409(manager):
    """Assign the same employee to two overlapping shifts and expect 409 with violations."""


@TODO
def test_absence_opens_shift_and_recommendations_exclude_absent(manager):
    """Integration: report absence -> shift is open -> absent employee isn't recommended."""
