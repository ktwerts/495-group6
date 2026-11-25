"""Scheduling module tests. Owner: Lead Architect.

The constraint functions are pure, so test them directly without the database.
"""

from datetime import date, timedelta

import pytest

from app.db import get_db
from app.errors import ValidationError
from app.scheduling import constraints
from app.scheduling import service as scheduling

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


def test_reporting_absence_reopens_shift_and_updates_staff_count(app, manager):
    created = manager.post("/api/employees", json={"name": "Alex Chen", "position": "Cook"})
    assert created.status_code == 201
    employee_id = created.get_json()["id"]

    availability = manager.post(
        f"/api/employees/{employee_id}/availability",
        json={"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"},
    )
    assert availability.status_code == 201

    created_shift = manager.post(
        "/api/shifts",
        json={
            "date": "2026-11-17",
            "start_time": "09:00",
            "end_time": "17:00",
        },
    )
    assert created_shift.status_code == 201
    shift_id = created_shift.get_json()["id"]

    assigned = manager.post(
        f"/api/shifts/{shift_id}/assign",
        json={"employee_id": employee_id},
    )
    assert assigned.status_code == 200

    with app.app_context():
        assert scheduling.count_scheduled_staff("2026-11-17") == 1

    absence = manager.post(
        "/api/absences",
        json={"employee_id": employee_id, "date": "2026-11-17"},
    )
    assert absence.status_code == 201

    shifts = manager.get("/api/shifts?start=2026-11-17&end=2026-11-17").get_json()
    shift = next(item for item in shifts if item["id"] == shift_id)
    assert shift["status"] == "open"
    assert shift["employee_id"] is None

    with app.app_context():
        assert scheduling.count_scheduled_staff("2026-11-17") == 0
        recorded = (
            get_db()
            .execute(
                "SELECT employee_id, date FROM absences WHERE employee_id = ?",
                (employee_id,),
            )
            .fetchone()
        )
        assert recorded is not None
        assert recorded["date"] == "2026-11-17"

    reassigned = manager.post(
        f"/api/shifts/{shift_id}/assign",
        json={"employee_id": employee_id},
    )
    assert reassigned.status_code == 409
    assert "Employee has a reported absence on this date." in (reassigned.get_json()["violations"])


def test_absence_route_requires_manager(client, staff):
    payload = {"employee_id": 1, "date": "2026-11-17"}

    assert staff.post("/api/absences", json=payload).status_code == 403

    staff.post("/api/auth/logout")
    assert client.post("/api/absences", json=payload).status_code == 401


def test_absence_rejects_unknown_employee(manager):
    response = manager.post(
        "/api/absences",
        json={"employee_id": 999999, "date": "2026-11-17"},
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"date": "2026-11-17"},
        {"employee_id": 1},
        {"employee_id": 1, "date": "11/17/2026"},
    ],
)
def test_absence_rejects_invalid_input(manager, payload):
    response = manager.post("/api/absences", json=payload)

    assert response.status_code == 400


def test_absence_opens_shift_and_recommendations_exclude_absent(app, manager):
    absent_id = add_employee(app, name="Alex Chen")
    replacement_id = add_employee(app, name="Sam Rivera")
    add_employee(app, name="Inactive Employee", active=0)
    add_employee(app, name="Unqualified Employee", qualifications="[]")

    shift_id = create(manager)
    assert assign(manager, shift_id, absent_id).status_code == 200

    absence = manager.post(
        "/api/absences",
        json={"employee_id": absent_id, "date": SHIFT["date"]},
    )
    assert absence.status_code == 201

    response = manager.get(f"/api/shifts/{shift_id}/recommendations")

    assert response.status_code == 200
    recommendations = response.get_json()
    assert [item["employee_id"] for item in recommendations] == [replacement_id]

    shifts = manager.get("/api/shifts").get_json()
    shift = next(item for item in shifts if item["id"] == shift_id)
    assert shift["status"] == "open"
    assert shift["employee_id"] is None


def test_recommendations_exclude_unavailable_busy_and_over_limit_employees(app, manager):
    available_id = add_employee(app, name="Available Employee")
    busy_id = add_employee(app, name="Busy Employee")
    add_employee(app, name="Over Limit Employee", max_hours=4)
    unavailable_id = add_employee(app, name="Unavailable Employee")

    with app.app_context():
        db = get_db()
        db.execute(
            "DELETE FROM availability WHERE employee_id = ?",
            (unavailable_id,),
        )
        db.commit()

    busy_shift_id = create(manager)
    assert assign(manager, busy_shift_id, busy_id).status_code == 200
    open_shift_id = create(manager)

    response = manager.get(f"/api/shifts/{open_shift_id}/recommendations")

    assert response.status_code == 200
    assert [item["employee_id"] for item in response.get_json()] == [available_id]


def test_manager_approval_assigns_replacement_and_restores_staff_count(app, manager):
    absent_id = add_employee(app, name="Alex Chen")
    replacement_id = add_employee(app, name="Sam Rivera")
    shift_id = create(manager)
    assert assign(manager, shift_id, absent_id).status_code == 200

    absence = manager.post(
        "/api/absences",
        json={"employee_id": absent_id, "date": SHIFT["date"]},
    )
    assert absence.status_code == 201

    recommendations = manager.get(f"/api/shifts/{shift_id}/recommendations")
    assert recommendations.status_code == 200
    assert replacement_id in [item["employee_id"] for item in recommendations.get_json()]

    with app.app_context():
        assert scheduling.count_scheduled_staff(SHIFT["date"]) == 0

    approved = manager.post(
        f"/api/shifts/{shift_id}/recommendations/approve",
        json={"employee_id": replacement_id},
    )

    assert approved.status_code == 200
    shift = approved.get_json()
    assert shift["employee_id"] == replacement_id
    assert shift["status"] == "assigned"

    with app.app_context():
        assert scheduling.count_scheduled_staff(SHIFT["date"]) == 1


def test_approval_rechecks_eligibility_and_preserves_existing_coverage(app, manager):
    first_id = add_employee(app, name="Sam Rivera")
    second_id = add_employee(app, name="Casey Morgan")
    shift_id = create(manager)

    recommended = manager.get(f"/api/shifts/{shift_id}/recommendations")
    assert recommended.status_code == 200
    assert first_id in [item["employee_id"] for item in recommended.get_json()]

    absence = manager.post(
        "/api/absences",
        json={"employee_id": first_id, "date": SHIFT["date"]},
    )
    assert absence.status_code == 201

    url = f"/api/shifts/{shift_id}/recommendations/approve"
    rejected = manager.post(url, json={"employee_id": first_id})
    assert rejected.status_code == 409

    approved = manager.post(url, json={"employee_id": second_id})
    assert approved.status_code == 200

    repeated = manager.post(url, json={"employee_id": second_id})
    assert repeated.status_code == 409

    shifts = manager.get("/api/shifts").get_json()
    shift = next(item for item in shifts if item["id"] == shift_id)
    assert shift["employee_id"] == second_id
    assert shift["status"] == "assigned"


def test_no_eligible_replacement_returns_empty_list_and_leaves_shift_open(app, manager):
    absent_id = add_employee(app, name="Alex Chen")
    add_employee(app, name="Unqualified Employee", qualifications="[]")
    shift_id = create(manager)
    assert assign(manager, shift_id, absent_id).status_code == 200

    absence = manager.post(
        "/api/absences",
        json={"employee_id": absent_id, "date": SHIFT["date"]},
    )
    assert absence.status_code == 201

    response = manager.get(f"/api/shifts/{shift_id}/recommendations")

    assert response.status_code == 200
    assert response.get_json() == []

    shifts = manager.get("/api/shifts").get_json()
    shift = next(item for item in shifts if item["id"] == shift_id)
    assert shift["status"] == "open"
    assert shift["employee_id"] is None

    with app.app_context():
        assert scheduling.count_scheduled_staff(SHIFT["date"]) == 0


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", "/api/shifts/1/recommendations", None),
        (
            "POST",
            "/api/shifts/1/recommendations/approve",
            {"employee_id": 1},
        ),
    ],
)
def test_replacement_routes_require_manager(client, staff, method, path, payload):
    response = staff.open(path, method=method, json=payload)
    assert response.status_code == 403

    staff.post("/api/auth/logout")

    response = client.open(path, method=method, json=payload)
    assert response.status_code == 401


def test_replacement_routes_reject_unknown_shift(manager):
    recommendations = manager.get("/api/shifts/999999/recommendations")
    assert recommendations.status_code == 404

    approval = manager.post(
        "/api/shifts/999999/recommendations/approve",
        json={"employee_id": 1},
    )
    assert approval.status_code == 404


@pytest.mark.parametrize("limit", ["0", "51", "invalid"])
def test_recommendations_reject_invalid_limit(app, manager, limit):
    add_employee(app)
    shift_id = create(manager)

    response = manager.get(f"/api/shifts/{shift_id}/recommendations?limit={limit}")

    assert response.status_code == 400


def test_assignment_respects_weekly_limit_entered_through_employee_api(manager):
    created = manager.post(
        "/api/employees",
        json={
            "name": "Part-Time Employee",
            "position": "Host",
            "max_weekly_hours": 6,
        },
    )
    assert created.status_code == 201
    employee_id = created.get_json()["id"]

    availability = manager.post(
        f"/api/employees/{employee_id}/availability",
        json={"day_of_week": 1, "start_time": "08:00", "end_time": "18:00"},
    )
    assert availability.status_code == 201

    first_id = create(
        manager,
        start_time="08:00",
        end_time="12:00",
        required_qualification="",
    )
    assert assign(manager, first_id, employee_id).status_code == 200

    second_id = create(
        manager,
        start_time="13:00",
        end_time="16:00",
        required_qualification="",
    )
    response = assign(manager, second_id, employee_id)

    assert response.status_code == 409
    assert any("weekly limit" in violation for violation in response.get_json()["violations"])

    shifts = manager.get("/api/shifts").get_json()
    second = next(shift for shift in shifts if shift["id"] == second_id)
    assert second["status"] == "open"
    assert second["employee_id"] is None


@pytest.mark.parametrize(
    ("new_limit", "expected_status", "saved_limit"),
    [(3, 409, 6), (4, 200, 4)],
)
def test_weekly_limit_edit_respects_upcoming_schedule(
    manager, new_limit, expected_status, saved_limit
):
    day = date.today() + timedelta(days=7)
    created = manager.post(
        "/api/employees",
        json={
            "name": "Part-Time Employee",
            "position": "Host",
            "max_weekly_hours": 6,
        },
    )
    assert created.status_code == 201
    employee_id = created.get_json()["id"]

    availability = manager.post(
        f"/api/employees/{employee_id}/availability",
        json={
            "day_of_week": day.weekday(),
            "start_time": "08:00",
            "end_time": "18:00",
        },
    )
    assert availability.status_code == 201

    shift_id = create(
        manager,
        date=day.isoformat(),
        start_time="08:00",
        end_time="12:00",
        required_qualification="",
    )
    assert assign(manager, shift_id, employee_id).status_code == 200

    response = manager.patch(
        f"/api/employees/{employee_id}/weekly-hours",
        json={"max_weekly_hours": new_limit},
    )

    assert response.status_code == expected_status

    employees = manager.get("/api/employees").get_json()
    saved = next(employee for employee in employees if employee["id"] == employee_id)
    assert saved["max_weekly_hours"] == saved_limit


def report(manager, employee_id, **extra):
    return manager.post(
        "/api/absences",
        json={"employee_id": employee_id, "date": SHIFT["date"], **extra},
    )


def test_duplicate_absence_is_rejected(app, manager):
    employee_id = add_employee(app)

    assert report(manager, employee_id).status_code == 201
    assert report(manager, employee_id).status_code == 409
    with app.app_context():
        count = get_db().execute("SELECT COUNT(*) FROM absences").fetchone()[0]
    assert count == 1


def test_absence_stores_optional_reason(app, manager):
    employee_id = add_employee(app)

    created = report(manager, employee_id, reason="  Sick  ")

    assert created.status_code == 201
    assert created.get_json()["reason"] == "Sick"
    with app.app_context():
        stored = get_db().execute("SELECT reason FROM absences").fetchone()["reason"]
    assert stored == "Sick"


@pytest.mark.parametrize("reason", [123, "x" * 201])
def test_absence_rejects_bad_reason(app, manager, reason):
    employee_id = add_employee(app)

    assert report(manager, employee_id, reason=reason).status_code == 400


def test_cancelled_absence_makes_employee_eligible_again(app, manager):
    employee_id = add_employee(app)
    shift_id = create(manager)
    assert assign(manager, shift_id, employee_id).status_code == 200

    absence_id = report(manager, employee_id).get_json()["id"]
    assert assign(manager, shift_id, employee_id).status_code == 409

    cancelled = manager.delete(f"/api/absences/{absence_id}")
    assert cancelled.status_code == 200
    assert cancelled.get_json()["id"] == absence_id

    # The reopened shift stays open until the manager reassigns it.
    assert manager.get("/api/shifts").get_json()[0]["status"] == "open"
    assert assign(manager, shift_id, employee_id).status_code == 200


def test_cancel_unknown_absence_returns_404(manager):
    assert manager.delete("/api/absences/999999").status_code == 404


def test_cancel_absence_is_manager_only(client, staff):
    assert staff.delete("/api/absences/1").status_code == 403
    staff.post("/api/auth/logout")
    assert client.delete("/api/absences/1").status_code == 401


def test_count_scheduled_staff_between_groups_by_date(app, manager):
    first = add_employee(app, name="First")
    second = add_employee(app, name="Second")
    morning = create(manager, start_time="09:00", end_time="12:00")
    afternoon = create(manager, start_time="13:00", end_time="16:00")
    assert assign(manager, morning, first).status_code == 200
    assert assign(manager, afternoon, first).status_code == 200
    assert assign(manager, create(manager), second).status_code == 200
    create(manager, date="2026-11-18")

    with app.app_context():
        counts = scheduling.count_scheduled_staff_between("2026-11-16", "2026-11-18")

    assert counts == {"2026-11-17": 2}


@pytest.mark.parametrize(
    ("start", "end"),
    [("2026-11-18", "2026-11-17"), ("11/17/2026", "2026-11-18"), ("2026-11-17", None)],
)
def test_count_scheduled_staff_between_rejects_bad_range(app, start, end):
    with app.app_context(), pytest.raises(ValidationError):
        scheduling.count_scheduled_staff_between(start, end)
