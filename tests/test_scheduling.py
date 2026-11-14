"""Scheduling module tests. Owner: Lead Architect.

These are templates: remove the skip marker as you implement each feature.
The constraint functions are pure, so test them directly without the database.
"""

import pytest

from app.scheduling import constraints

TODO = pytest.mark.skip(reason="TODO: implement scheduling module")


@TODO
def test_times_overlap():
    assert constraints.times_overlap("09:00", "12:00", "11:00", "13:00")
    assert not constraints.times_overlap("09:00", "12:00", "12:00", "15:00")


@TODO
def test_check_assignment_detects_missing_qualification():
    """check_assignment() should return a violation when the qualification is missing."""


@TODO
def test_create_shift_rejects_end_before_start(manager):
    """POST a shift whose end is before its start and expect 400."""


@TODO
def test_conflicting_assignment_returns_409(manager):
    """Assign the same employee to two overlapping shifts and expect 409 with violations."""


@TODO
def test_absence_opens_shift_and_recommendations_exclude_absent(manager):
    """Integration: report absence -> shift is open -> absent employee isn't recommended."""
