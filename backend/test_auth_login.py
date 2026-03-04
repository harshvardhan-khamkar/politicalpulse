from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import router
from app.database import get_db


def _build_client(monkeypatch):
    app = FastAPI()
    app.include_router(router)

    def fake_db():
        yield object()

    app.dependency_overrides[get_db] = fake_db

    user = SimpleNamespace(id=1, username="alice", role="user")

    def fake_authenticate_user(_, identifier, password):
        if password != "secret123":
            return None
        if identifier in {"alice", "alice@example.com"}:
            return user
        return None

    monkeypatch.setattr("app.api.auth.authenticate_user", fake_authenticate_user)
    monkeypatch.setattr(
        "app.api.auth.create_access_token",
        lambda data, expires_delta=None: "test-token",
    )

    return TestClient(app)


def test_login_with_username_and_password(monkeypatch):
    client = _build_client(monkeypatch)
    response = client.post(
        "/auth/login",
        data={"username": "alice", "password": "secret123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "test-token"
    assert payload["token_type"] == "bearer"


def test_login_with_email_and_password(monkeypatch):
    client = _build_client(monkeypatch)
    response = client.post(
        "/auth/login",
        data={"email": "alice@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "test-token"
    assert payload["token_type"] == "bearer"


def test_login_with_json_email_and_password(monkeypatch):
    client = _build_client(monkeypatch)
    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "test-token"
    assert payload["token_type"] == "bearer"


def test_login_with_missing_identifier_returns_422(monkeypatch):
    client = _build_client(monkeypatch)
    response = client.post(
        "/auth/login",
        data={"password": "secret123"},
    )

    assert response.status_code == 422
