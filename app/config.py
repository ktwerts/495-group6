"""Configuration management.

All secrets and environment-specific values come from environment variables
(see .env.example). Nothing sensitive is hardcoded.
"""

import os
import secrets


class Config:
    # If no key is provided a random one is generated, which logs everyone out
    # whenever the server restarts. Set SHIFTWISE_SECRET_KEY for anything shared.
    SECRET_KEY = os.environ.get("SHIFTWISE_SECRET_KEY") or secrets.token_hex(32)
    DATABASE = os.environ.get("SHIFTWISE_DATABASE")  # default: instance/shiftwise.sqlite
    MODEL_PATH = os.environ.get("SHIFTWISE_MODEL_PATH")  # default: instance/staffing_model.joblib

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Minimum days of staffing history before the ML model is used.
    # Below this, forecasting falls back to a weekday average.
    FORECAST_MIN_HISTORY = int(os.environ.get("SHIFTWISE_FORECAST_MIN_HISTORY", "28"))
    FORECAST_MAX_DAYS = 31

    # Failed logins allowed per client IP (Flask-Limiter syntax). Only 401s count.
    LOGIN_RATE_LIMIT = os.environ.get("SHIFTWISE_LOGIN_RATE_LIMIT", "5 per minute")
    # Failed logins allowed per username across all IPs, so spreading guesses over
    # many addresses is still slowed down.
    LOGIN_USERNAME_RATE_LIMIT = os.environ.get("SHIFTWISE_LOGIN_USERNAME_RATE_LIMIT", "20 per hour")
    # Flask-Limiter reads this; set SHIFTWISE_RATELIMIT_ENABLED=0 to turn limiting off.
    RATELIMIT_ENABLED = os.environ.get("SHIFTWISE_RATELIMIT_ENABLED", "1") != "0"

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-only-secret-key"  # noqa: S105 - used only by the test suite


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    REQUIRE_SECRET_KEY = True  # create_app() refuses to start without SHIFTWISE_SECRET_KEY


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    name = name or os.environ.get("SHIFTWISE_ENV", "development")
    try:
        return _CONFIGS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown config '{name}'. Use one of: {', '.join(_CONFIGS)}") from exc
