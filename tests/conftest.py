"""Shared test fixtures. Each test gets a fresh temporary database."""

import pytest

from app import create_app
from app.auth.service import create_user
from app.db import init_db

MANAGER = {"username": "manager", "password": "manager-pass-123"}
STAFF = {"username": "staff", "password": "staff-pass-123"}


@pytest.fixture
def app(tmp_path):
    app = create_app(
        "testing",
        {
            "DATABASE": str(tmp_path / "test.sqlite"),
            "MODEL_PATH": str(tmp_path / "model.joblib"),
        },
    )
    with app.app_context():
        init_db()
        create_user(MANAGER["username"], MANAGER["password"], "manager")
        create_user(STAFF["username"], STAFF["password"], "employee")
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def manager(client):
    """A test client logged in as a manager."""
    assert client.post("/api/auth/login", json=MANAGER).status_code == 200
    return client


@pytest.fixture
def staff(client):
    """A test client logged in as a regular employee."""
    assert client.post("/api/auth/login", json=STAFF).status_code == 200
    return client
