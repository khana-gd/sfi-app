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


def test_google_mock_login_success_matching_domain():
    email = "test-google-matching@kanha.local"
    response = client.post(
        "/api/v1/auth/google-mock",
        json={"id_token": email}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["role"] == "STUDENT"


def test_google_mock_login_pending_non_matching_domain():
    email = "test-google-non-matching@gmail.com"
    response = client.post(
        "/api/v1/auth/google-mock",
        json={"id_token": email}
    )
    assert response.status_code == 400
    assert "pending administrator approval" in response.json()["detail"]


def test_google_login_invalid_or_unconfigured():
    response = client.post(
        "/api/v1/auth/google",
        json={"id_token": "invalid-token"}
    )
    assert response.status_code == 400


def test_admin_approve_pending_user():
    # 1. Login as Admin to get Admin token
    admin_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@kanha.local", "password": "KanhaDevPass2026!"}
    )
    assert admin_res.status_code == 200
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Trigger mock google sign-in with non-matching domain (creates pending user)
    pending_email = "new-student-pending@gmail.com"
    pending_res = client.post(
        "/api/v1/auth/google-mock",
        json={"id_token": pending_email}
    )
    assert pending_res.status_code == 400
    assert "pending administrator approval" in pending_res.json()["detail"]

    # 3. Retrieve user list as admin to find the pending user's ID
    users_res = client.get("/api/v1/users/", headers=admin_headers)
    assert users_res.status_code == 200
    users_list = users_res.json()
    pending_user = next(u for u in users_list if u["email"] == pending_email)
    assert pending_user["is_active"] is False

    # 4. Activate the pending user
    activate_res = client.put(
        f"/api/v1/users/{pending_user['id']}/activate",
        headers=admin_headers
    )
    assert activate_res.status_code == 200
    assert activate_res.json()["is_active"] is True

    # 5. Now try to log in again using google-mock for this user
    success_res = client.post(
        "/api/v1/auth/google-mock",
        json={"id_token": pending_email}
    )
    assert success_res.status_code == 200
    assert "access_token" in success_res.json()
    assert success_res.json()["role"] == "STUDENT"


