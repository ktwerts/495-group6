"""Shifts, absences and replacement recommendations.

Owner: Lead Architect

This module sits between employees and forecasting:
- it calls employees.service (e.g. get_availability) to check who can work
- forecasting.service calls count_scheduled_staff() to compare predictions with the schedule

Tips:
- Use constraints.check_assignment() before saving any assignment.
- Raise ConflictError(message, violations) when a rule is broken -> 409 JSON response.
- Managers must approve recommendations before they take effect (proposal requirement).
- Delete each `raise NotImplementedError` as you implement the function.
"""

from app.db import get_db  # noqa: F401  (you'll need this)


def list_shifts(start: str | None = None, end: str | None = None) -> list[dict]:
    """Return shifts (optionally within a date range), including the assigned employee's name."""
    raise NotImplementedError("scheduling.list_shifts")


def create_shift(data: dict) -> dict:
    """Validate and create a shift; if an employee is given, check constraints first."""
    raise NotImplementedError("scheduling.create_shift")


def count_scheduled_staff(on_date: str) -> int:
    """How many employees are scheduled on a date (YYYY-MM-DD).

    Integration point: the forecasting module uses this to compute staffing gaps.
    """
    raise NotImplementedError("scheduling.count_scheduled_staff")


def count_scheduled_staff_between(start: str, end: str) -> dict[str, int]:
    """Scheduled staff for every date from start to end (inclusive), in one query.

    Returns {"YYYY-MM-DD": count}; dates with nobody scheduled can be left out (counted as 0).
    Integration point: forecasting uses this when it exists, and falls back to
    count_scheduled_staff() once per day until then.
    """
    raise NotImplementedError("scheduling.count_scheduled_staff_between")


def recommend_replacements(shift_id: int, limit: int = 3) -> list[dict]:
    """Rank employees who could legally cover an open shift (for manager approval)."""
    raise NotImplementedError("scheduling.recommend_replacements")
