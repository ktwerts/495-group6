"""ShiftWise AI - intelligent workforce scheduling.

Application factory. Each feature area lives in its own module (blueprint):

    auth         -> login, sessions, role-based access
    employees    -> employee records and availability
    scheduling   -> shifts, absences, constraint checks, replacement recommendations
    forecasting  -> AI staffing-demand prediction (scikit-learn)
"""

import logging
import os

from flask import Flask, render_template

from app.config import get_config


def create_app(config_name: str | None = None, overrides: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(config_name))
    if overrides:
        app.config.update(overrides)

    if app.config.get("REQUIRE_SECRET_KEY") and not os.environ.get("SHIFTWISE_SECRET_KEY"):
        raise RuntimeError("SHIFTWISE_SECRET_KEY must be set in production")
    app.logger.setLevel(logging.INFO)

    os.makedirs(app.instance_path, exist_ok=True)
    if not app.config.get("DATABASE"):
        app.config["DATABASE"] = os.path.join(app.instance_path, "shiftwise.sqlite")
    if not app.config.get("MODEL_PATH"):
        app.config["MODEL_PATH"] = os.path.join(app.instance_path, "staffing_model.joblib")

    from app import db
    from app.errors import register_error_handlers

    db.init_app(app)
    register_error_handlers(app)

    from app.auth.routes import bp as auth_bp
    from app.employees.routes import bp as employees_bp
    from app.forecasting.routes import bp as forecasting_bp
    from app.scheduling.routes import bp as scheduling_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(scheduling_bp)
    app.register_blueprint(forecasting_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
