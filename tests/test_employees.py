"""Employees module tests. Owner: Interface Designer.

These are templates: remove the skip marker as you implement each feature, then
fill in the test. Aim for a success case plus invalid-input and permission cases.
Fixtures available: client, manager (logged-in manager), staff (logged-in employee).
"""

import pytest

TODO = pytest.mark.skip(reason="TODO: implement employees module")


@TODO
def test_create_employee(manager):
    res = manager.post("/api/employees", json={"name": "Sam", "position": "Cook"})
    assert res.status_code == 201


@TODO
def test_create_employee_rejects_missing_name(manager):
    assert manager.post("/api/employees", json={"position": "Cook"}).status_code == 400


@TODO
def test_list_employees(manager):
    assert manager.get("/api/employees").status_code == 200


@TODO
def test_availability_validation(manager):
    """Bad day numbers or start >= end should return 400."""


@TODO
def test_employee_can_only_view_own_record(staff):
    """An employee-role user gets 403 when viewing someone else's record."""
