"""Forecasting HTTP routes. Keep these thin: parse the request, call service, return JSON."""

from datetime import date

from flask import Blueprint, jsonify, render_template, request

from app.auth.decorators import role_required
from app.forecasting import service
from app.validation import parse_date, parse_int

bp = Blueprint("forecasting", __name__)


@bp.get("/forecast")
@role_required("manager")
def forecast_page():
    return render_template("forecast.html")


@bp.get("/api/forecast")
@role_required("manager")
def forecast():
    start_arg = request.args.get("start")
    start = parse_date(start_arg, "start") if start_arg else date.today()
    days = parse_int(request.args.get("days", 7), "days", minimum=1, maximum=31)
    return jsonify(service.forecast(start, days))


@bp.post("/api/forecast/train")
@role_required("manager")
def train():
    return jsonify(service.train_model())
