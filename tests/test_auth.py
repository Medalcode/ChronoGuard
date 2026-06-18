import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app

# Use a file-based SQLite to avoid in-memory connection issues
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
SQLALCHEMY_TEST_DATABASE_URL = f"sqlite:///{_db_path}"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

GOOD_PASSWORD = "SecureP@ss123"


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestHealth:
    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestRegister:
    def test_register_user(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": GOOD_PASSWORD},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "vault_salt" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": GOOD_PASSWORD},
        )
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "AnotherP@ss123"},
        )
        assert response.status_code == 400
        assert "ya está registrado" in response.json()["detail"]

    def test_register_weak_password_no_uppercase(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "securep@ss123"},
        )
        assert response.status_code == 422

    def test_register_weak_password_no_digit(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecureP@ssword"},
        )
        assert response.status_code == 422

    def test_register_weak_password_no_special_char(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecurePassword123"},
        )
        assert response.status_code == 422

    def test_register_weak_password_too_short(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "Sh1!"},
        )
        assert response.status_code == 422


class TestLogin:
    def _register(self, client, email="test@example.com", password=GOOD_PASSWORD):
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )

    def test_login_user(self, client):
        self._register(client)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": GOOD_PASSWORD},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "vault_salt" in data

    def test_login_wrong_password(self, client):
        self._register(client)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "WrongP@ss123"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": GOOD_PASSWORD},
        )
        assert response.status_code == 401

    def test_login_account_locked_after_attempts(self, client):
        self._register(client)
        for _ in range(6):
            client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "WrongP@ss123"},
            )
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "WrongP@ss123"},
        )
        assert response.status_code == 429
        assert "bloqueada" in response.json()["detail"]


class TestMe:
    def test_get_current_user(self, client):
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": GOOD_PASSWORD},
        )
        token = reg_resp.json()["access_token"]
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "vault_salt" in data
        assert "password_hash" not in data

    def test_get_current_user_invalid_token(self, client):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken123"},
        )
        assert response.status_code == 401


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    os.close(_db_fd)
    os.unlink(_db_path)
