"""User accounts. Passwords are stored only as salted hashes (werkzeug / scrypt)."""

import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db
from app.errors import ValidationError

ROLES = ("manager", "employee")
MIN_PASSWORD_LENGTH = 8


def create_user(username: str, password: str, role: str, employee_id: int | None = None) -> dict:
    username = (username or "").strip()
    if not username:
        raise ValidationError("username is required")
    if role not in ROLES:
        raise ValidationError(f"role must be one of: {', '.join(ROLES)}")
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO users (username, password_hash, role, employee_id) VALUES (?, ?, ?, ?)",
            (username, generate_password_hash(password), role, employee_id),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        raise ValidationError("username already exists or employee_id is invalid") from exc
    return {"id": cur.lastrowid, "username": username, "role": role, "employee_id": employee_id}


def authenticate(username: str, password: str) -> sqlite3.Row | None:
    user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        return None
    return user


def get_user(user_id: int) -> sqlite3.Row | None:
    return (
        get_db()
        .execute("SELECT id, username, role, employee_id FROM users WHERE id = ?", (user_id,))
        .fetchone()
    )
