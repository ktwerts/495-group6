"""Employees HTTP routes. Keep these thin: parse the request, call service, return JSON."""

from flask import Blueprint, jsonify, render_template

from app.auth.decorators import role_required
from app.employees import service

bp = Blueprint("employees", __name__)


@bp.get("/employees")
@role_required("manager")
def employees_page():
    return render_template("employees.html")


@bp.get("/api/employees")
@role_required("manager")
def list_employees():
    return jsonify(service.list_employees())


# TODO(Interface Designer): add the rest of the employee endpoints you define in
# docs/api-spec.md, for example create, get one, update, deactivate and set availability.
# Use @role_required("manager") for manager-only routes and the helpers in
# app/validation.py to parse input.
