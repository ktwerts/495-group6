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

from datetime import date, datetime

from app.db import get_db
from app.employees import service as employees
from app.errors import ConflictError, NotFoundError, ValidationError
from app.scheduling import constraints


def list_shifts(start: str | None = None, end: str | None = None) -> list[dict]:
    """Return scheduled shifts, optionally filtered by date."""

    # Validate optional date filters.
    for value in (start, end):
        if value is not None:
            try:
                date.fromisoformat(value)
            except (TypeError, ValueError):
                raise ValidationError("Dates must use YYYY-MM-DD format.") from None

    if start and end and start > end:
        raise ValidationError("Start date cannot be after end date.")

    db = get_db()

    query = """
        SELECT id, date, start_time, end_time,
               required_qualification, employee_id, status
        FROM shifts
        WHERE 1 = 1
    """
    parameters = []

    if start:
        query += " AND date >= ?"
        parameters.append(start)

    if end:
        query += " AND date <= ?"
        parameters.append(end)

    query += " ORDER BY date, start_time, id"

    rows = db.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]


def create_shift(data: dict) -> dict:
    """Create an open shift; assign an employee afterwards with assign_shift()."""

    if not isinstance(data, dict):
        raise ValidationError("Shift data must be an object.")

    for field in ("date", "start_time", "end_time"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValidationError(f"{field} is required.")

    qualification = data.get("required_qualification")
    if qualification is not None and not isinstance(qualification, str):
        raise ValidationError("required_qualification must be text.")
    qualification = (qualification or "").strip() or None

    try:
        shift_date = date.fromisoformat(data["date"])
        if shift_date.isoformat() != data["date"]:
            raise ValueError()
    except ValueError:
        raise ValidationError("Date must use YYYY-MM-DD format.") from None

    try:
        start = datetime.strptime(data["start_time"], "%H:%M")
        end = datetime.strptime(data["end_time"], "%H:%M")
    except ValueError:
        raise ValidationError("Times must use HH:MM format.") from None

    if start >= end:
        raise ValidationError("End time must be after start time.")

    if data.get("employee_id") is not None:
        raise ValidationError(
            "Create the shift first, then assign it with /api/shifts/<id>/assign."
        )

    db = get_db()

    cursor = db.execute(
        """
        INSERT INTO shifts
        (date, start_time, end_time,
         required_qualification, employee_id, status)
        VALUES (?, ?, ?, ?, NULL, 'open')
        """,
        (
            data["date"],
            start.strftime("%H:%M"),
            end.strftime("%H:%M"),
            qualification,
        ),
    )

    db.commit()
    return _get_shift(cursor.lastrowid)


def _get_shift(shift_id: int) -> dict:
    row = get_db().execute("SELECT * FROM shifts WHERE id = ?", (shift_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Shift {shift_id} not found")
    return dict(row)


def _get_employee(employee_id: int) -> dict:
    for employee in employees.list_employees(include_inactive=True):
        if employee["id"] == employee_id:
            return employee
    raise NotFoundError(f"Employee {employee_id} not found")


def assign_shift(shift_id: int, employee_id: int) -> dict:
    """Assign an employee to a shift, or raise ConflictError listing the rules it breaks."""
    shift = _get_shift(shift_id)
    if shift["status"] == "cancelled":
        raise ConflictError("Shift can't be assigned", ["Shift is cancelled."])
    employee = _get_employee(employee_id)

    db = get_db()
    monday, sunday = constraints.week_of(shift["date"])
    other_shifts = db.execute(
        """
        SELECT date, start_time, end_time FROM shifts
        WHERE employee_id = ? AND status = 'assigned' AND date BETWEEN ? AND ? AND id != ?
        """,
        (employee_id, monday, sunday, shift_id),
    ).fetchall()
    absences = db.execute(
        "SELECT date FROM absences WHERE employee_id = ? AND date = ?",
        (employee_id, shift["date"]),
    ).fetchall()

    violations = constraints.check_assignment(
        employee,
        shift,
        availability=employees.get_availability(employee_id),
        other_shifts=[dict(row) for row in other_shifts],
        absences=[dict(row) for row in absences],
    )
    if violations:
        raise ConflictError(f"{employee['name']} can't work this shift", violations)

    db.execute(
        "UPDATE shifts SET employee_id = ?, status = 'assigned' WHERE id = ?",
        (employee_id, shift_id),
    )
    db.commit()
    return _get_shift(shift_id)


def unassign_shift(shift_id: int) -> dict:
    """Remove the employee from a shift and reopen it."""
    shift = _get_shift(shift_id)
    if shift["status"] == "cancelled":
        raise ConflictError("Shift can't be reopened", ["Shift is cancelled."])
    db = get_db()
    db.execute("UPDATE shifts SET employee_id = NULL, status = 'open' WHERE id = ?", (shift_id,))
    db.commit()
    return _get_shift(shift_id)


def count_scheduled_staff(on_date: str) -> int:
    """Count distinct employees assigned to shifts on a date."""

    try:
        parsed_date = date.fromisoformat(on_date)
        if parsed_date.isoformat() != on_date:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValidationError("Date must use YYYY-MM-DD format.") from None

    db = get_db()

    row = db.execute(
        """
        SELECT COUNT(DISTINCT employee_id) AS total
        FROM shifts
        WHERE date = ?
          AND employee_id IS NOT NULL
          AND status = 'assigned'
        """,
        (on_date,),
    ).fetchone()

    return int(row["total"])


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
