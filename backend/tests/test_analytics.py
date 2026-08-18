import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_token(email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "KanhaDevPass2026!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def student1_headers():
    token = get_token("student1@kanha.local")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def faculty_headers():
    token = get_token("faculty@kanha.local")
    return {"Authorization": f"Bearer {token}"}

def test_student_progress_endpoint(student1_headers):
    response = client.get("/api/v1/analytics/student/progress", headers=student1_headers)
    assert response.status_code == 200
    data = response.json()
    assert "submission_stats" in data
    assert "attendance_rate" in data
    assert "portfolio_items_count" in data
    assert "grade_trend" in data

def test_faculty_warnings_and_rbac(student1_headers, faculty_headers):
    # 1. Verify student cannot access faculty warnings
    response = client.get("/api/v1/analytics/faculty/warnings", headers=student1_headers)
    assert response.status_code == 403

    # 2. Verify faculty can access warnings
    response = client.get("/api/v1/analytics/faculty/warnings", headers=faculty_headers)
    assert response.status_code == 200
    warnings = response.json()
    assert isinstance(warnings, list)
    
    # 3. Publish an overdue assignment targeted to Student 1's batch (Batch ID 1)
    # This automatically triggers the "Unfinished overdue work" flag trigger since student1 has no submission
    assignment_payload = {
        "title": "Overdue Pattern Making",
        "description": "Create a pattern blocks overview",
        "deadline": "2025-01-01T12:00:00",
        "priority": "HIGH",
        "category": "Pattern Drafting",
        "start_date": "2024-12-01T12:00:00",
        "target_type": "BATCH",
        "target_id": 1  # Batch 1
    }
    response = client.post("/api/v1/assignments/", json=assignment_payload, headers=faculty_headers)
    assert response.status_code == 200
    
    # Publish another overdue assignment to trigger total_overdue > 1
    assignment_payload2 = {
        "title": "Overdue Draping 2",
        "description": "Draping patterns review",
        "deadline": "2025-01-02T12:00:00",
        "priority": "HIGH",
        "category": "Draping",
        "start_date": "2024-12-01T12:00:00",
        "target_type": "BATCH",
        "target_id": 1  # Batch 1
    }
    response = client.post("/api/v1/assignments/", json=assignment_payload2, headers=faculty_headers)
    assert response.status_code == 200

    # 4. Verify that Student 1 is now flagged in the faculty watchlist due to overdue work (>1 overdue assignments)
    response = client.get("/api/v1/analytics/faculty/warnings", headers=faculty_headers)
    assert response.status_code == 200
    warnings = response.json()
    
    # Find student 1 (Aarav) or student 2 (Vihaan) who are both in Batch 1
    flagged_emails = [w["email"] for w in warnings]
    assert "student1@kanha.local" in flagged_emails
    
    # Verify flagged reason mentions overdue work
    student1_warning = next(w for w in warnings if w["email"] == "student1@kanha.local")
    assert any("overdue work" in r.lower() for r in student1_warning["reasons"])
