"""Employees HTTP routes. Keep these thin: parse the request, call service, return JSON."""

from flask import Blueprint, jsonify, render_template, request

from app.auth.decorators import role_required
from app.db import get_db
from app.employees import service
from app.scheduling import service as scheduling
from app.validation import require_json

bp = Blueprint("employees", __name__)


@bp.get("/employees")
@role_required("manager")
def employees_page():
    return render_template("employees.html")


@bp.get("/api/employees")
@role_required("manager")
def list_employees():
    return jsonify(service.list_employees())


@bp.post("/api/employees")
@role_required("manager")
def create_employee():
    data = require_json(request.get_json(silent=True))
    return jsonify(service.create_employee(data)), 201


@bp.post("/api/employees/<int:employee_id>/availability")
@role_required("manager")
def add_availability(employee_id: int):
    data = require_json(request.get_json(silent=True))
    return jsonify(service.add_availability(employee_id, data)), 201


@bp.patch("/api/employees/<int:employee_id>/weekly-hours")
@role_required("manager")
def update_weekly_hours(employee_id: int):
    data = require_json(request.get_json(silent=True))
    proposed_limit = service.validate_weekly_hours(data.get("max_weekly_hours"))

    db = get_db()
    with db:
        db.execute("BEGIN IMMEDIATE")
        scheduling.validate_weekly_hour_limit(employee_id, proposed_limit)
        employee = service.update_weekly_hours(employee_id, data)

    return jsonify(employee)


# TODO(Interface Designer): add the rest of the employee endpoints you define in
# docs/api-spec.md, for example create, get one, update, deactivate and set availability.
# Use @role_required("manager") for manager-only routes and the helpers in
# app/validation.py to parse input.
