"""Employees module tests. Owner: Interface Designer.

These are templates: remove the skip marker as you implement each feature, then
fill in the test. Aim for a success case plus invalid-input and permission cases.
Fixtures available: client, manager (logged-in manager), staff (logged-in employee).
"""

import pytest

from app.db import get_db
from app.employees.service import get_availability


def test_create_employee(manager):
    response = manager.post("/api/employees", json={"name": "Sam", "position": "Cook"})

    assert response.status_code == 201
    employee = response.get_json()
    assert employee == {
        "id": employee["id"],
        "name": "Sam",
        "position": "Cook",
        "qualifications": [],
        "max_weekly_hours": 40,
        "availability": [],
        "active": 1,
    }

    employee_list = manager.get("/api/employees")
    assert employee_list.status_code == 200
    assert employee in employee_list.get_json()


def test_create_employee_saves_custom_weekly_hours(manager):
    response = manager.post(
        "/api/employees",
        json={
            "name": "Alex Chen",
            "position": "Cook",
            "max_weekly_hours": 20,
        },
    )

    assert response.status_code == 201
    employee = response.get_json()
    assert employee["max_weekly_hours"] == 20

    employees = manager.get("/api/employees").get_json()
    saved = next(item for item in employees if item["id"] == employee["id"])
    assert saved["max_weekly_hours"] == 20


def test_create_employee_rejects_missing_name(manager):
    assert manager.post("/api/employees", json={"position": "Cook"}).status_code == 400


@pytest.mark.parametrize("field", ["name", "position"])
def test_create_employee_rejects_fields_over_100_characters(manager, field):
    employee = {"name": "Alex Chen", "position": "Cook"}
    employee[field] = "A" * 101

    response = manager.post("/api/employees", json=employee)

    assert response.status_code == 400
    assert field in response.get_json()["error"]


def test_manager_can_add_employee_availability(manager):
    created = manager.post("/api/employees", json={"name": "Alex Chen", "position": "Cook"})
    assert created.status_code == 201
    employee_id = created.get_json()["id"]
    slot = {"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"}

    response = manager.post(f"/api/employees/{employee_id}/availability", json=slot)
    assert response.status_code == 201

    employees = manager.get("/api/employees").get_json()
    alex = next(employee for employee in employees if employee["id"] == employee_id)
    assert alex["availability"] == [slot]


def test_add_availability_rejects_unknown_employee(manager):
    slot = {"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"}

    response = manager.post("/api/employees/999999/availability", json=slot)

    assert response.status_code == 404
    assert response.get_json()["error"]


@pytest.mark.parametrize(
    ("start", "end"),
    [("09:00", "12:00"), ("11:00", "14:00")],
    ids=["duplicate", "overlap"],
)
def test_add_availability_rejects_conflicting_slot(manager, start, end):
    created = manager.post("/api/employees", json={"name": "Alex Chen", "position": "Cook"})
    assert created.status_code == 201
    employee_id = created.get_json()["id"]
    url = f"/api/employees/{employee_id}/availability"
    existing_slot = {"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"}
    assert manager.post(url, json=existing_slot).status_code == 201

    slot = {"day_of_week": 0, "start_time": start, "end_time": end}
    response = manager.post(url, json=slot)

    assert response.status_code == 409
    assert response.get_json()["error"]


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


@pytest.mark.parametrize(
    "slot",
    [
        {"day_of_week": 7, "start_time": "09:00", "end_time": "17:00"},
        {"day_of_week": 0, "start_time": "17:00", "end_time": "09:00"},
    ],
)
def test_availability_validation(manager, slot):
    created = manager.post("/api/employees", json={"name": "Alex Chen", "position": "Cook"})
    assert created.status_code == 201
    employee_id = created.get_json()["id"]

    response = manager.post(f"/api/employees/{employee_id}/availability", json=slot)

    assert response.status_code == 400


@pytest.mark.skip(
    reason="Deferred: Alpha provides manager-only employee management; "
    "an employee self-service record endpoint is not implemented."
)
def test_employee_can_only_view_own_record(staff):
    """Future self-service endpoint must restrict access to the employee's own record."""


@pytest.mark.parametrize(
    "limit",
    [0, -1, 169, True, None, "twenty", "20"],
)
def test_create_employee_rejects_invalid_weekly_hours(manager, limit):
    response = manager.post(
        "/api/employees",
        json={
            "name": "Alex Chen",
            "position": "Cook",
            "max_weekly_hours": limit,
        },
    )

    assert response.status_code == 400
    assert "max_weekly_hours" in response.get_json()["error"]
    assert manager.get("/api/employees").get_json() == []


def test_manager_can_update_employee_weekly_hours(manager):
    created = manager.post(
        "/api/employees",
        json={"name": "Alex Chen", "position": "Cook"},
    )
    assert created.status_code == 201
    employee_id = created.get_json()["id"]

    response = manager.patch(
        f"/api/employees/{employee_id}/weekly-hours",
        json={"max_weekly_hours": 20},
    )

    assert response.status_code == 200
    assert response.get_json()["max_weekly_hours"] == 20

    employees = manager.get("/api/employees").get_json()
    saved = next(employee for employee in employees if employee["id"] == employee_id)
    assert saved["max_weekly_hours"] == 20
    assert saved["name"] == "Alex Chen"
    assert saved["position"] == "Cook"


@pytest.mark.parametrize("limit", [0, -1, 169, True, None, "20"])
def test_update_weekly_hours_rejects_invalid_limit(manager, limit):
    created = manager.post(
        "/api/employees",
        json={
            "name": "Alex Chen",
            "position": "Cook",
            "max_weekly_hours": 20,
        },
    )
    assert created.status_code == 201
    employee_id = created.get_json()["id"]

    response = manager.patch(
        f"/api/employees/{employee_id}/weekly-hours",
        json={"max_weekly_hours": limit},
    )

    assert response.status_code == 400
    assert "max_weekly_hours" in response.get_json()["error"]

    employees = manager.get("/api/employees").get_json()
    saved = next(employee for employee in employees if employee["id"] == employee_id)
    assert saved["max_weekly_hours"] == 20


def test_update_weekly_hours_requires_manager(client, staff):
    url = "/api/employees/1/weekly-hours"
    payload = {"max_weekly_hours": 20}

    assert staff.patch(url, json=payload).status_code == 403

    staff.post("/api/auth/logout")
    assert client.patch(url, json=payload).status_code == 401


def test_update_weekly_hours_rejects_unknown_employee(manager):
    response = manager.patch(
        "/api/employees/999999/weekly-hours",
        json={"max_weekly_hours": 20},
    )

    assert response.status_code == 404
