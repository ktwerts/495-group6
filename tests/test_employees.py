"""Employees module tests. Owner: Interface Designer.

These are templates: remove the skip marker as you implement each feature, then
fill in the test. Aim for a success case plus invalid-input and permission cases.
Fixtures available: client, manager (logged-in manager), staff (logged-in employee).
"""

import pytest

from app.db import get_db
from app.employees.service import get_availability

TODO = pytest.mark.skip(reason="TODO: implement employees module")


@TODO
def test_create_employee(manager):
    res = manager.post("/api/employees", json={"name": "Sam", "position": "Cook"})
    assert res.status_code == 201


@TODO
def test_create_employee_rejects_missing_name(manager):
    assert manager.post("/api/employees", json={"position": "Cook"}).status_code == 400


def test_list_employees(manager):
    response = manager.get("/api/employees")

    assert response.status_code == 200
    assert response.get_json() == []


def test_list_employees_returns_only_active_records(app, manager):
    with app.app_context():
        db = get_db()
        db.executemany(
            "INSERT INTO employees "
            "(name, position, qualifications, max_weekly_hours, active) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                ("Sam Rivera", "Cook", '["food safety"]', 32, 1),
                ("Alex Chen", "Cook", "[]", 24, 0),
            ],
        )
        db.execute(
            """
            INSERT INTO availability (employee_id, day_of_week, start_time, end_time)
            SELECT id, ?, ?, ? FROM employees WHERE name = ?
            """,
            (0, "09:00", "17:00", "Sam Rivera"),
        )
        db.commit()

    response = manager.get("/api/employees")

    assert response.status_code == 200
    employees = response.get_json()
    assert len(employees) == 1
    assert employees[0]["name"] == "Sam Rivera"
    assert employees[0]["position"] == "Cook"
    assert employees[0]["qualifications"] == ["food safety"]
    assert employees[0]["max_weekly_hours"] == 32
    assert employees[0]["availability"] == [
        {"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"}
    ]


def test_get_availability_returns_only_the_requested_employees_slots(app):
    with app.app_context():
        db = get_db()
        employee_ids = []
        for name in ("Sam Rivera", "Alex Chen"):
            employee = db.execute(
                "INSERT INTO employees (name, position, max_weekly_hours) VALUES (?, ?, ?)",
                (name, "Cook", 32),
            )
            employee_ids.append(employee.lastrowid)

        sam_id, alex_id = employee_ids
        db.execute(
            """
            INSERT INTO availability (employee_id, day_of_week, start_time, end_time)
            VALUES (?, ?, ?, ?)
            """,
            (sam_id, 0, "09:00", "17:00"),
        )

        assert get_availability(sam_id) == [
            {"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"}
        ]
        assert get_availability(alex_id) == []


@TODO
def test_availability_validation(manager):
    """Bad day numbers or start >= end should return 400."""


@TODO
def test_employee_can_only_view_own_record(staff):
    """An employee-role user gets 403 when viewing someone else's record."""
