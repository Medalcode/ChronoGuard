"""
Ejemplo de prueba rápida para verificar que todo está conectado correctamente.
Ejecuta con: pytest tests/test_auth.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app

# Crear una BD en memoria para testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Crea tablas para testing y proporciona una sesión."""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Crea un cliente de test con BD en memoria."""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_check(client):
    """Verifica que el endpoint /health funciona."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user(client):
    """Verifica que se puede registrar un usuario."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "SecurePassword123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "vault_salt" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    """Verifica que no se puede registrar el mismo email dos veces."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "SecurePassword123"},
    )

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "AnotherPassword123"},
    )

    assert response.status_code == 400
    assert "ya está registrado" in response.json()["detail"]


def test_login_user(client):
    """Verifica que se puede hacer login tras registrarse."""
    # Primero registramos
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "SecurePassword123"},
    )

    # Luego hacemos login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "SecurePassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "vault_salt" in data
