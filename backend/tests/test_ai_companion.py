import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db.models import StudentIssue, FacultyProfile

client = TestClient(app)


def get_token(email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "KanhaDevPass2026!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_level1_ai_response():
    # 1. Login as Student 1
    token = get_token("student1@kanha.local")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Post a student doubt ticket
    payload = {
        "category": "ASSIGNMENT_HELP",
        "description": "How do I format Mughal Costume Sketches borders?",
        "assignment_id": 1
    }
    response = client.post("/api/v1/issues/", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Verify Level 1 AI responses
    assert data["escalation_level"] == 1
    assert data["status"] == "OPEN"

    # Fetch the issue detail to verify AI response was appended to the thread
    detail_res = client.get(f"/api/v1/issues/{data['id']}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    
    # Must have 2 messages: Student's query + AI reply
    assert len(detail_data["messages"]) == 2
    assert detail_data["messages"][0]["is_ai_response"] is False
    assert detail_data["messages"][1]["is_ai_response"] is True
    assert "Mughal costume" in detail_data["messages"][1]["content"]


def test_distress_detection_escalation():
    token = get_token("student1@kanha.local")
    headers = {"Authorization": f"Bearer {token}"}

    # Post query containing distress crisis keywords
    payload = {
        "category": "INSTRUCTION_HELP",
        "description": "I am having a severe mental breakdown and cannot cope with illustration drawings.",
        "assignment_id": 1
    }
    response = client.post("/api/v1/issues/", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Distress should trigger immediate Level 3 escalation
    assert data["escalation_level"] == 3
    assert data["status"] == "ESCALATED"

    # Verify fixed reassurance message was appended immediately
    detail_res = client.get(f"/api/v1/issues/{data['id']}", headers=headers)
    messages = detail_res.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["is_ai_response"] is False
    assert messages[1]["is_ai_response"] is True
    assert "reassurance" in messages[1]["content"].lower() or "988" in messages[1]["content"]


def test_grading_dispute_escalation():
    token = get_token("student1@kanha.local")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "category": "GRADING_DISPUTE",
        "description": "I feel my Mughal Costume Sketches grade was unfairly deducted.",
        "assignment_id": 1
    }
    response = client.post("/api/v1/issues/", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Grading dispute should trigger immediate Level 3 escalation
    assert data["escalation_level"] == 3
    assert data["status"] == "ESCALATED"

    # Verify no AI messages were appended
    detail_res = client.get(f"/api/v1/issues/{data['id']}", headers=headers)
    assert len(detail_res.json()["messages"]) == 1


def test_escalate_and_draft_ownership_scopes():
    # 1. Login users
    student1_token = get_token("student1@kanha.local")
    student2_token = get_token("student2@kanha.local")
    faculty_token = get_token("faculty@kanha.local")
    admin_token = get_token("admin@kanha.local")

    # 2. Student 1 creates a normal doubt ticket
    payload = {
        "category": "ASSIGNMENT_HELP",
        "description": "Textile surface ornamentation layout draft query.",
        "assignment_id": 1
    }
    res = client.post("/api/v1/issues/", json=payload, headers={"Authorization": f"Bearer {student1_token}"})
    assert res.status_code == 200
    issue_id = res.json()["id"]

    # 3. Ownership Check 1: Student 2 tries to escalate Student 1's ticket -> 403 Forbidden
    res_esc_unauth = client.post(
        f"/api/v1/issues/{issue_id}/escalate",
        headers={"Authorization": f"Bearer {student2_token}"}
    )
    assert res_esc_unauth.status_code == 403

    # 4. Student 1 escalates own ticket -> 200 OK (Updates escalation_level to 2)
    res_esc_auth = client.post(
        f"/api/v1/issues/{issue_id}/escalate",
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert res_esc_auth.status_code == 200
    assert res_esc_auth.json()["escalation_level"] == 2
    assert res_esc_auth.json()["status"] == "ESCALATED"

    # 5. Ownership Check 2: Student 1 tries to fetch the Level 2 draft response -> 403 Forbidden (Student role cannot access drafts)
    res_draft_student = client.get(
        f"/api/v1/issues/{issue_id}/draft",
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert res_draft_student.status_code == 403

    # 6. Assigned Faculty member requests the draft -> 200 OK with draft suggestion
    res_draft_fac1 = client.get(
        f"/api/v1/issues/{issue_id}/draft",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res_draft_fac1.status_code == 200
    assert "draft" in res_draft_fac1.json()

    # 7. Ownership Check 3: Another Faculty member (Faculty 2) tries to fetch the draft -> 403 Forbidden
    # Dynamically register Faculty 2
    unique_email = f"fac_copilot_{uuid.uuid4().hex[:6]}@kanha.local"
    reg_payload = {
        "email": unique_email,
        "password": "KanhaDevPass2026!",
        "first_name": "Prof. Copilot",
        "last_name": "Reviewer",
        "role": "FACULTY",
        "is_active": True
    }
    reg_response = client.post(
        "/api/v1/users",
        json=reg_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reg_response.status_code == 200
    faculty2_token = get_token(unique_email)

    res_draft_fac2 = client.get(
        f"/api/v1/issues/{issue_id}/draft",
        headers={"Authorization": f"Bearer {faculty2_token}"}
    )
    assert res_draft_fac2.status_code == 403
