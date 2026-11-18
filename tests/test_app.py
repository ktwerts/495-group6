import pytest

from app import create_app
from app.scheduling import service as scheduling


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_unknown_api_route_returns_json_404(client):
    res = client.get("/api/does-not-exist")
    assert res.status_code == 404
    assert "error" in res.get_json()


def test_home_page_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"ShiftWise AI" in res.data


def test_manager_pages_render(manager):
    for path in ("/employees", "/schedule", "/forecast"):
        assert manager.get(path).status_code == 200, path


def test_pages_redirect_to_login_when_logged_out(client):
    res = client.get("/schedule")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_production_requires_secret_key(monkeypatch, tmp_path):
    monkeypatch.delenv("SHIFTWISE_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_app("production", {"DATABASE": str(tmp_path / "p.sqlite")})
    monkeypatch.setenv("SHIFTWISE_SECRET_KEY", "x" * 64)
    assert create_app("production", {"DATABASE": str(tmp_path / "p.sqlite")}).config[
        "SESSION_COOKIE_SECURE"
    ]


def test_unknown_config_name_rejected():
    with pytest.raises(ValueError):
        create_app("staging")


def test_wrong_method_returns_json_405(client):
    res = client.get("/api/auth/login")
    assert res.status_code == 405
    assert "error" in res.get_json()


def test_unimplemented_stub_returns_json_501(manager, monkeypatch):
    """Stubs raise NotImplementedError; the API reports that clearly instead of crashing."""

    def stub(*args):
        raise NotImplementedError("scheduling.list_shifts")

    monkeypatch.setattr(scheduling, "list_shifts", stub)
    res = manager.get("/api/shifts")
    assert res.status_code == 501
    assert "Not implemented yet" in res.get_json()["error"]


def test_seed_command(app, monkeypatch):
    monkeypatch.setenv("SHIFTWISE_ADMIN_PASSWORD", "demo-password-1")
    result = app.test_cli_runner().invoke(args=["seed"])
    assert result.exit_code == 0, result.output
    client = app.test_client()
    login = {"username": "manager", "password": "demo-password-1"}
    assert client.post("/api/auth/login", json=login).status_code == 200
    response = client.get("/api/employees")

    assert response.status_code == 200
    assert any(employee["name"] == "Sam Rivera" for employee in response.get_json())


def test_seed_creates_employee_login(app, monkeypatch):
    monkeypatch.setenv("SHIFTWISE_EMPLOYEE_PASSWORD", "demo-employee-test")
    result = app.test_cli_runner().invoke(args=["seed"])
    assert result.exit_code == 0, result.output

    client = app.test_client()
    login = {"username": "employee", "password": "demo-employee-test"}
    response = client.post("/api/auth/login", json=login)
    assert response.status_code == 200
    assert response.get_json()["role"] == "employee"

    profile = client.get("/api/auth/me")
    assert profile.status_code == 200
    assert profile.get_json()["employee_id"] is not None


def test_seed_generates_password_when_unset(app, monkeypatch):
    monkeypatch.delenv("SHIFTWISE_ADMIN_PASSWORD", raising=False)
    result = app.test_cli_runner().invoke(args=["seed"])
    assert "Generated password" in result.output


def test_init_db_command(app):
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert "Initialized" in result.output
