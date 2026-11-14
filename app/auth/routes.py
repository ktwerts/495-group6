from flask import Blueprint, g, jsonify, render_template, request, session

from app.auth import service
from app.auth.decorators import login_required, role_required
from app.validation import require_fields, require_json

bp = Blueprint("auth", __name__)


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = service.get_user(user_id) if user_id is not None else None


@bp.get("/login")
def login_page():
    return render_template("login.html")


@bp.post("/api/auth/login")
def login():
    data = require_json(request.get_json(silent=True))
    require_fields(data, "username", "password")
    user = service.authenticate(str(data["username"]).strip(), str(data["password"]))
    if user is None:
        return jsonify(error="Invalid username or password"), 401

    session.clear()
    session["user_id"] = user["id"]
    return jsonify(id=user["id"], username=user["username"], role=user["role"])


@bp.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out")


@bp.get("/api/auth/me")
@login_required
def me():
    return jsonify(dict(g.user))


@bp.post("/api/auth/users")
@role_required("manager")
def create_user():
    data = require_json(request.get_json(silent=True))
    require_fields(data, "username", "password", "role")
    user = service.create_user(
        data["username"], str(data["password"]), data["role"], data.get("employee_id")
    )
    return jsonify(user), 201
