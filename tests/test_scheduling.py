"""Scheduling module tests. Owner: Lead Architect.

The constraint functions are pure, so test them directly without the database.
"""

import pytest

from app.db import get_db
from app.scheduling import constraints

SHIFT = {
    "date": "2026-11-17",
    "start_time": "09:00",
    "end_time": "17:00",
    "required_qualification": "Cashier",
}


def test_shift_routes_are_manager_only(client, staff):
    assert staff.get("/api/shifts").status_code == 403
    assert staff.post("/api/shifts", json=SHIFT).status_code == 403
    staff.post("/api/auth/logout")
    assert client.get("/api/shifts").status_code == 401
    assert client.post("/api/shifts", json=SHIFT).status_code == 401


def test_create_shift_requires_json_object(manager):
    assert manager.post("/api/shifts", json=["not", "an", "object"]).status_code == 400


def test_list_shifts_filters_by_date(manager):
    for day in ("2026-11-16", "2026-11-17", "2026-11-18"):
        assert manager.post("/api/shifts", json={**SHIFT, "date": day}).status_code == 201

    res = manager.get("/api/shifts?start=2026-11-17&end=2026-11-18")
    assert [shift["date"] for shift in res.get_json()] == ["2026-11-17", "2026-11-18"]
    assert manager.get("/api/shifts?start=2026-11-18&end=2026-11-17").status_code == 400
    assert manager.get("/api/shifts?start=11/17/2026").status_code == 400


TODO = pytest.mark.skip(reason="TODO: implement scheduling module")


def test_times_overlap():
    assert constraints.times_overlap("09:00", "12:00", "11:00", "13:00")
    assert not constraints.times_overlap("09:00", "12:00", "12:00", "15:00")


def test_check_assignment_detects_missing_qualification():
    """Check that an employee has the required qualification."""

    employee = {"active": True, "qualifications": ["Cashier"]}

    shift = {
        "date": "2026-11-17",
        "start_time": "09:00",
        "end_time": "17:00",
        "required_qualification": "Manager",
    }

    availability = [{"day_of_week": 1, "start_time": "08:00", "end_time": "18:00"}]

    violations = constraints.check_assignment(employee, shift, availability=availability)

    assert "Employee does not have the required qualification." in violations


def test_create_shift_rejects_end_before_start():
    """Reject shifts that end before they start."""
    from app.errors import ValidationError
    from app.scheduling.service import create_shift

    shift = {
        "date": "2026-11-17",
        "start_time": "17:00",
        "end_time": "09:00",
        "required_qualification": "Cashier",
    }

    with pytest.raises(ValidationError):
        create_shift(shift)


def test_create_shift_normalizes_single_digit_hour(app):
    """Store single-digit hours in HH:MM format."""
    from app.scheduling.service import create_shift

    with app.app_context():
        shift = create_shift(
            {
                "date": "2026-11-17",
                "start_time": "9:00",
                "end_time": "17:00",
                "required_qualification": "Cashier",
            }
        )

    assert shift["start_time"] == "09:00"
    assert shift["end_time"] == "17:00"
    assert shift["status"] == "open"


def test_count_scheduled_staff_counts_assigned_employees(app):
    """Count distinct assigned employees, excluding open and cancelled shifts."""
    from app.db import get_db
    from app.scheduling.service import count_scheduled_staff

    with app.app_context():
        db = get_db()

        db.executemany(
            """
            INSERT INTO shifts
            (date, start_time, end_time, required_qualification, employee_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("2026-11-17", "09:00", "12:00", "Cashier", 1, "assigned"),
                ("2026-11-17", "13:00", "17:00", "Cashier", 1, "assigned"),
                ("2026-11-17", "09:00", "12:00", "Cashier", 2, "assigned"),
                ("2026-11-17", "09:00", "12:00", "Cashier", None, "open"),
                ("2026-11-17", "09:00", "12:00", "Cashier", 3, "cancelled"),
            ],
        )
        db.commit()

        assert count_scheduled_staff("2026-11-17") == 2


def test_single_digit_time_overlap():
    """A single-digit start hour should not bypass overlap detection."""
    assert constraints.times_overlap("9:00", "9:30", "09:15", "09:45")


def add_employee(app, name="Alex Chen", qualifications='["cashier"]', active=1, max_hours=40):
    """Employee available Tuesdays 08:00-18:00 (2026-11-17 is a Tuesday)."""
    with app.app_context():
        db = get_db()
        employee_id = db.execute(
            "INSERT INTO employees (name, position, qualifications, max_weekly_hours, active)"
            " VALUES (?, 'Cashier', ?, ?, ?)",
            (name, qualifications, max_hours, active),
        ).lastrowid
        db.execute(
            "INSERT INTO availability (employee_id, day_of_week, start_time, end_time)"
            " VALUES (?, 1, '08:00', '18:00')",
            (employee_id,),
        )
        db.commit()
    return employee_id


def create(manager, **changes):
    res = manager.post("/api/shifts", json={**SHIFT, **changes})
    assert res.status_code == 201
    return res.get_json()["id"]


def assign(manager, shift_id, employee_id):
    return manager.post(f"/api/shifts/{shift_id}/assign", json={"employee_id": employee_id})


def test_assign_shift_marks_it_assigned(app, manager):
    employee_id = add_employee(app)
    shift_id = create(manager)

    res = assign(manager, shift_id, employee_id)
    assert res.status_code == 200
    assert res.get_json()["employee_id"] == employee_id
    assert res.get_json()["status"] == "assigned"
    assert manager.get("/api/shifts").get_json()[0]["status"] == "assigned"


def test_qualification_match_ignores_case(app, manager):
    employee_id = add_employee(app, qualifications='["cashier"]')
    assert (
        assign(manager, create(manager, required_qualification="CASHIER"), employee_id).status_code
        == 200
    )


def test_shift_without_qualification_can_go_to_anyone_available(app, manager):
    employee_id = add_employee(app, qualifications="[]")
    assert (
        assign(manager, create(manager, required_qualification=""), employee_id).status_code == 200
    )


def test_conflicting_assignment_returns_409(app, manager):
    employee_id = add_employee(app)
    assert assign(manager, create(manager), employee_id).status_code == 200

    res = assign(manager, create(manager, start_time="12:00", end_time="15:00"), employee_id)
    assert res.status_code == 409
    assert "Employee already has an overlapping shift." in res.get_json()["violations"]


@pytest.mark.parametrize(
    ("changes", "violation"),
    [
        ({"date": "2026-11-18"}, "Employee is not available for the entire shift."),
        ({"start_time": "07:00"}, "Employee is not available for the entire shift."),
        (
            {"required_qualification": "forklift"},
            "Employee does not have the required qualification.",
        ),
    ],
)
def test_assignment_breaking_a_rule_returns_409(app, manager, changes, violation):
    employee_id = add_employee(app)
    res = assign(manager, create(manager, **changes), employee_id)
    assert res.status_code == 409
    assert violation in res.get_json()["violations"]
    assert manager.get("/api/shifts").get_json()[0]["status"] == "open"


def test_assignment_over_weekly_hours_returns_409(app, manager):
    employee_id = add_employee(app, max_hours=8)
    first = create(manager, start_time="08:00", end_time="14:00")
    assert assign(manager, first, employee_id).status_code == 200

    res = assign(manager, create(manager, start_time="14:00", end_time="18:00"), employee_id)
    assert res.status_code == 409
    assert res.get_json()["violations"] == [
        "Shift would put the employee over their weekly limit (10 of 8 hours)."
    ]


def weekly_check(other_shifts, limit=20, day="2026-11-17"):
    employee = {"active": True, "qualifications": [], "max_weekly_hours": limit}
    shift = {"date": day, "start_time": "09:00", "end_time": "17:00"}
    availability = [{"day_of_week": 1, "start_time": "08:00", "end_time": "18:00"}]
    return constraints.check_assignment(
        employee, shift, availability=availability, other_shifts=other_shifts
    )


def test_weekly_limit_allows_exactly_reaching_it():
    monday = {"date": "2026-11-16", "start_time": "08:00", "end_time": "20:00"}
    assert weekly_check([monday]) == []


def test_weekly_limit_only_counts_the_same_week():
    last_sunday = {"date": "2026-11-15", "start_time": "06:00", "end_time": "23:00"}
    next_monday = {"date": "2026-11-23", "start_time": "06:00", "end_time": "23:00"}
    assert weekly_check([last_sunday, next_monday]) == []

    saturday = {"date": "2026-11-21", "start_time": "06:00", "end_time": "19:00"}
    assert "weekly limit (21 of 20 hours)" in weekly_check([saturday])[0]


def test_inactive_or_absent_employee_cannot_be_assigned(app, manager):
    inactive = add_employee(app, name="Former", active=0)
    absent = add_employee(app, name="Away")
    with app.app_context():
        get_db().execute(
            "INSERT INTO absences (employee_id, date) VALUES (?, '2026-11-17')", (absent,)
        )
        get_db().commit()

    assert (
        "Employee is inactive."
        in assign(manager, create(manager), inactive).get_json()["violations"]
    )
    assert (
        "Employee has a reported absence on this date."
        in assign(manager, create(manager), absent).get_json()["violations"]
    )


def test_assign_unknown_shift_or_employee_returns_404(app, manager):
    employee_id = add_employee(app)
    assert assign(manager, 999, employee_id).status_code == 404
    assert assign(manager, create(manager), 999).status_code == 404


@pytest.mark.parametrize("body", [{}, {"employee_id": "abc"}, {"employee_id": 0}, ["x"]])
def test_assign_rejects_bad_body(manager, body):
    shift_id = create(manager)
    assert manager.post(f"/api/shifts/{shift_id}/assign", json=body).status_code == 400


def test_unassign_reopens_shift(app, manager):
    employee_id = add_employee(app)
    shift_id = create(manager)
    assign(manager, shift_id, employee_id)

    res = manager.post(f"/api/shifts/{shift_id}/unassign")
    assert res.status_code == 200
    assert res.get_json()["status"] == "open"
    assert res.get_json()["employee_id"] is None


def test_cancelled_shift_cannot_be_assigned_or_reopened(app, manager):
    employee_id = add_employee(app)
    shift_id = create(manager)
    with app.app_context():
        get_db().execute("UPDATE shifts SET status = 'cancelled' WHERE id = ?", (shift_id,))
        get_db().commit()
    assert assign(manager, shift_id, employee_id).status_code == 409
    assert manager.post(f"/api/shifts/{shift_id}/unassign").status_code == 409


def test_create_shift_rejects_employee_id(manager):
    assert manager.post("/api/shifts", json={**SHIFT, "employee_id": 1}).status_code == 400


def test_assign_routes_are_manager_only(client, staff):
    assert staff.post("/api/shifts/1/assign", json={"employee_id": 1}).status_code == 403
    assert staff.post("/api/shifts/1/unassign").status_code == 403
    staff.post("/api/auth/logout")
    assert client.post("/api/shifts/1/assign", json={"employee_id": 1}).status_code == 401


@TODO
def test_absence_opens_shift_and_recommendations_exclude_absent(manager):
    """Report absence, reopen shift, and exclude absent employee."""
