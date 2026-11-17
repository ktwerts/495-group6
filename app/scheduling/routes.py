"""Scheduling HTTP routes. Keep these thin: parse the request, call service, return JSON."""

from flask import Blueprint, jsonify, render_template, request
from app.auth.decorators import role_required
from app.scheduling import service

bp = Blueprint("scheduling", __name__)


@bp.get("/schedule")
@role_required("manager")
def schedule_page():
    return render_template("schedule.html")


@bp.get("/api/shifts")
@role_required("manager")
def list_shifts():
    return jsonify(service.list_shifts())


# TODO(Lead Architect): add the remaining scheduling endpoints from docs/api-spec.md,
# for example create shift, assign/unassign, report absence, recommend replacements,
# and approve/reject a recommendation.
@bp.post("/api/shifts")
@role_required("manager")
def create_shift():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        from app.errors import ValidationError
        raise ValidationError("A JSON object is required.")

    shift = service.create_shift(data)
    return jsonify(shift), 201