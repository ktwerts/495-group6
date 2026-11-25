"""Rate limiting for authentication requests.

Failed logins are limited per client IP and per submitted username; the numbers come
from app config. Counters are in memory: they reset on restart and are not shared
between workers (TD-1).
"""

from flask import current_app, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
    headers_enabled=True,
)


def login_limit() -> str:
    """The per-IP failed-login limit for the running app (Config.LOGIN_RATE_LIMIT)."""
    return current_app.config["LOGIN_RATE_LIMIT"]


def username_login_limit() -> str:
    """The per-username failed-login limit (Config.LOGIN_USERNAME_RATE_LIMIT)."""
    return current_app.config["LOGIN_USERNAME_RATE_LIMIT"]


def login_username_key() -> str:
    """Key a login attempt by its username, ignoring case and surrounding spaces."""
    data = request.get_json(silent=True)
    username = data.get("username") if isinstance(data, dict) else None
    if isinstance(username, str) and username.strip():
        return f"user:{username.strip().casefold()}"
    return f"ip:{get_remote_address()}"


def failed_login(response) -> bool:
    """Only rejected credentials (401) count against the limits."""
    return response.status_code == 401
