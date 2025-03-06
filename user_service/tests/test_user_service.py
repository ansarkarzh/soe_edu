import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from database import Base, get_db
from app import app, get_password_hash
from models import User as UserModel

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_register_user():
    response = client.post(
        "/register",
        json={"login": "testuser", "password": "testpassword", "email": "test@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["login"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_register_duplicate_login():
    response = client.post(
        "/register",
        json={"login": "duplicate", "password": "testpassword", "email": "duplicate@example.com"},
    )
    assert response.status_code == 200
    
    response = client.post(
        "/register",
        json={"login": "duplicate", "password": "testpassword", "email": "different@example.com"},
    )
    assert response.status_code == 400
    assert "уже зарегистрирован" in response.json()["detail"]

def test_login():
    response = client.post(
        "/register",
        json={"login": "logintest", "password": "testpassword", "email": "login@example.com"},
    )
    assert response.status_code == 200
    
    response = client.post(
        "/login",
        json={"login": "logintest", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post(
        "/login",
        json={"login": "nonexistent", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Неверный логин или пароль" in response.json()["detail"]

def test_token_endpoint():
    response = client.post(
        "/register",
        json={"login": "tokentest", "password": "testpassword", "email": "token@example.com"},
    )
    assert response.status_code == 200
    
    response = client.post(
        "/token",
        data={"username": "tokentest", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_update_user_profile():
    response = client.post(
        "/register",
        json={"login": "updatetest", "password": "testpassword", "email": "update@example.com"},
    )
    assert response.status_code == 200
    
    response = client.post(
        "/login",
        json={"login": "updatetest", "password": "testpassword"},
    )
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "first_name": "Test",
        "last_name": "User",
        "birth_date": "1990-01-01",
        "phone_number": "1234567890"
    }
    response = client.put("/users/me", headers=headers, json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["birth_date"] == "1990-01-01"
    assert data["phone_number"] == "1234567890"
