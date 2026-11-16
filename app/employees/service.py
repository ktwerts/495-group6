"""Employee business logic and data access.

Owner: Interface Designer

Other modules (scheduling, forecasting) should call functions in this file instead of
querying the employee tables directly. Agree on these signatures with the team, then
document them in docs/architecture.md.

Tips:
- Get a connection with get_db() and always use ? placeholders in SQL.
- Raise ValidationError for bad input and NotFoundError for missing records
  (app/errors.py turns them into 400 / 404 JSON responses).
- Delete each `raise NotImplementedError` as you implement the function.
"""

import json
from collections import defaultdict

from app.db import get_db  # noqa: F401  (you'll need this)


def list_employees(include_inactive: bool = False) -> list[dict]:
    """Return employee records, defaulting to active employees only."""
    rows = (
        get_db()
        .execute(
            """
        SELECT id, name, position, qualifications, max_weekly_hours, active
        FROM employees
        WHERE active = 1 OR ? = 1
        ORDER BY id
        """,
            (include_inactive,),
        )
        .fetchall()
    )
    availability_by_employee = defaultdict(list)
    slots = get_db().execute(
        """
        SELECT employee_id, day_of_week, start_time, end_time
        FROM availability
        ORDER BY employee_id, day_of_week, start_time, end_time
        """
    )
    for row in slots:
        slot = dict(row)
        employee_id = slot.pop("employee_id")
        availability_by_employee[employee_id].append(slot)
    employees = []
    for row in rows:
        employee = dict(row)
        employee["qualifications"] = json.loads(employee["qualifications"])
        employee["availability"] = availability_by_employee[employee["id"]]
        employees.append(employee)

    return employees


def get_employee(employee_id: int) -> dict:
    """Return one employee, or raise NotFoundError."""
    raise NotImplementedError("employees.get_employee")


def create_employee(data: dict) -> dict:
    """Validate input, insert an employee, and return it."""
    raise NotImplementedError("employees.create_employee")

def get_availability(employee_id: int) -> list[dict]:
    """Return the employee's recorded weekly availability slots."""
    rows = get_db().execute(
        """
        SELECT day_of_week, start_time, end_time
        FROM availability
        WHERE employee_id = ?
        ORDER BY day_of_week, start_time, end_time
        """,
        (employee_id,),
    )
    return [dict(row) for row in rows]
