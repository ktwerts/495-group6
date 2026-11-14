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

from app.db import get_db  # noqa: F401  (you'll need this)


def list_employees(include_inactive: bool = False) -> list[dict]:
    """Return employees as dicts (name, position, qualifications, max hours, availability)."""
    raise NotImplementedError("employees.list_employees")


def get_employee(employee_id: int) -> dict:
    """Return one employee, or raise NotFoundError."""
    raise NotImplementedError("employees.get_employee")


def create_employee(data: dict) -> dict:
    """Validate input, insert an employee, and return it."""
    raise NotImplementedError("employees.create_employee")


def get_availability(employee_id: int) -> list[dict]:
    """Return the employee's weekly availability slots.

    The scheduling module needs this to check whether someone can work a shift.
    """
    raise NotImplementedError("employees.get_availability")
