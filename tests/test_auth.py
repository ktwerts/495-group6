import time

from app import create_app
from app.db import get_db
from tests.conftest import MANAGER


def test_login_success_returns_role(client):
    res = client.post("/api/auth/login", json=MANAGER)
    assert res.status_code == 200
    assert res.get_json()["role"] == "manager"
    assert client.get("/api/auth/me").get_json()["username"] == "manager"


def test_login_wrong_password(client):
    res = client.post("/api/auth/login", json={"username": "manager", "password": "nope-nope"})
    assert res.status_code == 401


def test_repeated_failed_logins_are_rate_limited(client):
    credentials = {"username": "manager", "password": "incorrect-password"}

    for _ in range(5):
        response = client.post("/api/auth/login", json=credentials)
        assert response.status_code == 401

    blocked = client.post("/api/auth/login", json=credentials)

    assert blocked.status_code == 429
    assert blocked.is_json
    assert blocked.get_json()["error"]
    assert client.get("/api/auth/me").status_code == 401


def test_login_missing_fields(client):
    assert client.post("/api/auth/login", json={"username": "manager"}).status_code == 400
    assert client.post("/api/auth/login", data="not json").status_code == 400


def test_logout_clears_session(manager):
    manager.post("/api/auth/logout")
    assert manager.get("/api/auth/me").status_code == 401


def test_api_requires_login(client):
    assert client.get("/api/employees").status_code == 401


def test_employee_role_cannot_access_manager_endpoints(staff):
    assert staff.get("/api/employees").status_code == 403
    assert staff.get("/api/shifts").status_code == 403
    assert staff.get("/api/forecast").status_code == 403


def test_passwords_are_hashed(app):
    with app.app_context():
        row = (
            get_db()
            .execute("SELECT password_hash FROM users WHERE username = 'manager'")
            .fetchone()
        )
    assert MANAGER["password"] not in row["password_hash"]


def test_manager_can_create_user_with_validation(manager):
    ok = manager.post(
        "/api/auth/users", json={"username": "new", "password": "long-enough", "role": "employee"}
    )
    assert ok.status_code == 201
    short = manager.post(
        "/api/auth/users", json={"username": "x", "password": "short", "role": "employee"}
    )
    assert short.status_code == 400
    dup = manager.post(
        "/api/auth/users", json={"username": "new", "password": "long-enough", "role": "employee"}
    )
    assert dup.status_code == 400


def test_login_rate_limit_expires(client, monkeypatch):
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now)
    credentials = {"username": "manager", "password": "incorrect-password"}

    for _ in range(5):
        assert client.post("/api/auth/login", json=credentials).status_code == 401

    assert client.post("/api/auth/login", json=MANAGER).status_code == 429

    now += 61

    response = client.post("/api/auth/login", json=MANAGER)
    assert response.status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_successful_logins_do_not_consume_failure_allowance(client):
    for _ in range(6):
        response = client.post("/api/auth/login", json=MANAGER)
        assert response.status_code == 200
        assert client.post("/api/auth/logout").status_code == 200


def test_login_rate_limit_is_separate_for_each_ip(client):
    credentials = {"username": "manager", "password": "incorrect-password"}
    first_ip = {"REMOTE_ADDR": "192.0.2.1"}
    second_ip = {"REMOTE_ADDR": "192.0.2.2"}

    for _ in range(5):
        response = client.post(
            "/api/auth/login",
            json=credentials,
            environ_overrides=first_ip,
        )
        assert response.status_code == 401

    blocked = client.post(
        "/api/auth/login",
        json=MANAGER,
        environ_overrides=first_ip,
    )
    assert blocked.status_code == 429

    allowed = client.post(
        "/api/auth/login",
        json=MANAGER,
        environ_overrides=second_ip,
    )
    assert allowed.status_code == 200


def test_login_limit_comes_from_config(app, client):
    app.config["LOGIN_RATE_LIMIT"] = "2 per minute"
    credentials = {"username": "manager", "password": "incorrect-password"}

    for _ in range(2):
        assert client.post("/api/auth/login", json=credentials).status_code == 401

    assert client.post("/api/auth/login", json=MANAGER).status_code == 429


def test_failed_logins_for_one_username_are_limited_across_ips(app, client):
    app.config["LOGIN_USERNAME_RATE_LIMIT"] = "3 per minute"
    credentials = {"username": " Manager ", "password": "incorrect-password"}

    for number in range(3):
        response = client.post(
            "/api/auth/login",
            json=credentials,
            environ_overrides={"REMOTE_ADDR": f"192.0.2.{number + 10}"},
        )
        assert response.status_code == 401

    fresh_ip = {"REMOTE_ADDR": "192.0.2.50"}
    blocked = client.post("/api/auth/login", json=MANAGER, environ_overrides=fresh_ip)
    assert blocked.status_code == 429

    other_user = client.post(
        "/api/auth/login",
        json={"username": "staff", "password": "staff-pass-123"},
        environ_overrides=fresh_ip,
    )
    assert other_user.status_code == 200


def test_new_app_starts_with_empty_login_counters(app, client):
    credentials = {"username": "manager", "password": "incorrect-password"}
    for _ in range(5):
        assert client.post("/api/auth/login", json=credentials).status_code == 401
    assert client.post("/api/auth/login", json=MANAGER).status_code == 429

    fresh = create_app("testing", {"DATABASE": app.config["DATABASE"]})
    assert fresh.test_client().post("/api/auth/login", json=MANAGER).status_code == 200
