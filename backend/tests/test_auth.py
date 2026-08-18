from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "student1@kanha.local", "password": "KanhaDevPass2026!"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["role"] == "STUDENT"


def test_login_invalid_credentials():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "student1@kanha.local", "password": "wrongpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"
