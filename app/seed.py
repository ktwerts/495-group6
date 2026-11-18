"""Sample data for local development and demos (run with `flask seed`)."""

import os
import secrets
from datetime import date, timedelta

from app.auth.service import create_user
from app.db import get_db
from app.errors import ConflictError
from app.forecasting.history import seed_staffing_history
from app.scheduling import service as scheduling

# (name, position, qualifications, days of week, start, end)
EXTRA_EMPLOYEES = [
    ("Priya Patel", "Cook", '["food safety"]', range(7), "09:00", "17:00"),
    ("Jordan Lee", "Cashier", '["cashier"]', range(5), "08:00", "16:00"),
    ("Casey Morgan", "Host", "[]", range(7), "16:00", "22:00"),
]

# (start, end, required qualification, who to assign; None leaves it open for the demo)
DAILY_SHIFTS = [
    ("09:00", "13:00", "food safety", "Priya Patel"),
    ("13:00", "17:00", "food safety", "Sam Rivera"),
    ("10:00", "14:00", "cashier", "Jordan Lee"),
    ("17:00", "21:00", None, None),
]


def seed_all() -> tuple[str | None, str | None]:
    """Create demo data and return any generated passwords in manager, employee order."""
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
    employee_ids = {"Sam Rivera": employee.lastrowid}
    for name, position, qualifications, days, start, end in EXTRA_EMPLOYEES:
        employee_ids[name] = _add_employee(name, position, qualifications, days, start, end)
    seed_week_of_shifts(employee_ids)
    seed_staffing_history()
    return generated, generated_employee


def _add_employee(name, position, qualifications, days, start, end) -> int:
    db = get_db()
    employee_id = db.execute(
        """
        INSERT INTO employees (name, position, qualifications, max_weekly_hours)
        VALUES (?, ?, ?, ?)
        """,
        (name, position, qualifications, 40),
    ).lastrowid
    db.executemany(
        "INSERT INTO availability (employee_id, day_of_week, start_time, end_time)"
        " VALUES (?, ?, ?, ?)",
        [(employee_id, day, start, end) for day in days],
    )
    db.commit()
    return employee_id


def seed_week_of_shifts(employee_ids: dict[str, int], start: date | None = None) -> None:
    """Create 7 days of shifts from `start` (default today). Shifts whose employee isn't
    available that day stay open, so the forecast and schedule show real gaps."""
    start = start or date.today()
    for offset in range(7):
        day = (start + timedelta(days=offset)).isoformat()
        for shift_start, shift_end, qualification, name in DAILY_SHIFTS:
            shift = scheduling.create_shift(
                {
                    "date": day,
                    "start_time": shift_start,
                    "end_time": shift_end,
                    "required_qualification": qualification,
                }
            )
            if name is None:
                continue
            try:
                scheduling.assign_shift(shift["id"], employee_ids[name])
            except ConflictError:
                pass
