"""Sample data for local development and demos (run with `flask seed`)."""

import os
import secrets

from app.auth.service import create_user
from app.db import get_db


def seed_all() -> tuple[str | None, str | None]:
    """Create demo data and return any generated passwords in manager, employee order.

    TODO (each owner adds sample data for their module):
      - Lead Architect: a week of shifts (leave a few open to demo replacements)
      - Integration Lead: several months of staffing history for training the model
        (synthetic is fine for alpha; note it in docs/technical-debt.md)
    """
    password = os.environ.get("SHIFTWISE_ADMIN_PASSWORD")
    generated = None
    if not password:
        password = generated = secrets.token_urlsafe(12)
    create_user("manager", password, "manager")
    db = get_db()
    employee = db.execute(
        """
        INSERT INTO employees (name, position, qualifications, max_weekly_hours)
        VALUES (?, ?, ?, ?)
        """,
        ("Sam Rivera", "Cook", '["food safety"]', 32),
    )
    db.execute(
        """
        INSERT INTO availability (employee_id, day_of_week, start_time, end_time)
        VALUES (?, ?, ?, ?)
        """,
        (employee.lastrowid, 0, "09:00", "17:00"),
    )
    db.commit()
    employee_password = os.environ.get("SHIFTWISE_EMPLOYEE_PASSWORD")
    generated_employee = None
    if not employee_password:
        employee_password = generated_employee = secrets.token_urlsafe(12)

    create_user("employee", employee_password, "employee", employee.lastrowid)
    return generated, generated_employee
