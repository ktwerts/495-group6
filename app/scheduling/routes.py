"""Scheduling HTTP routes. Keep these thin: parse the request, call service, return JSON."""

from flask import Blueprint, jsonify, render_template, request

from app.auth.decorators import role_required
from app.scheduling import service
from app.validation import require_json

bp = Blueprint("scheduling", __name__)


@bp.get("/schedule")
@role_required("manager")
def schedule_page():
    return render_template("schedule.html")


@bp.get("/api/shifts")
@role_required("manager")
def list_shifts():
    return jsonify(service.list_shifts(request.args.get("start"), request.args.get("end")))


@bp.post("/api/shifts")
@role_required("manager")
def create_shift():
    data = require_json(request.get_json(silent=True))
    return jsonify(service.create_shift(data)), 201


# TODO(Lead Architect): assign/unassign, report absence, recommend replacements,
# and approve/reject a recommendation.
