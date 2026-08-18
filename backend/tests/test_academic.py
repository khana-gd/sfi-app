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


def test_academic_workflow():
    faculty_token = get_token("faculty@kanha.local")
    student1_token = get_token("student1@kanha.local")

    f_headers = {"Authorization": f"Bearer {faculty_token}"}
    s_headers = {"Authorization": f"Bearer {student1_token}"}

    # 1. Faculty creates a new targeted assignment (batch 1, student 1)
    # student1 profile ID is 1, batch ID is 1
    assign_payload = {
        "title": "Draping Technique Basics",
        "description": "Construct a basic cowl neckline sample using muslin.",
        "deadline": "2026-08-30T18:00:00Z",
        "priority": "MEDIUM",
        "category": "Draping",
        "batch_ids": [1],
        "student_ids": [1]
    }
    a_res = client.post("/api/v1/assignments", json=assign_payload, headers=f_headers)
    assert a_res.status_code == 200
    assignment_id = a_res.json()["id"]

    # 2. Student 1 queries assignments -> Should contain the newly created draping assignment
    s_list_res = client.get("/api/v1/assignments", headers=s_headers)
    assert s_list_res.status_code == 200
    titles = [a["title"] for a in s_list_res.json()]
    assert "Draping Technique Basics" in titles

    # 3. Student 1 uploads a submission
    # We use multipart form encoding to simulate file upload
    sub_data = {
        "assignment_id": assignment_id,
        "submission_text": "I used a lightweight cotton muslin. Drape is clean."
    }
    # Send request with no file first
    sub_res = client.post("/api/v1/submissions/", data=sub_data, headers=s_headers)
    assert sub_res.status_code == 200
    submission_id = sub_res.json()["id"]
    assert sub_res.json()["status"] == "SUBMITTED"

    # 4. Faculty reviews the submission, posting feedback (REVISION_REQUIRED)
    fb_payload = {
        "feedback_text": "The cowl draping folds are slightly uneven. Need revision.",
        "grade": "C+"
    }
    fb_res = client.post(f"/api/v1/submissions/{submission_id}/feedback", json=fb_payload, headers=f_headers)
    assert fb_res.status_code == 200
    assert fb_res.json()["grade"] == "C+"

    # Check that submission status updated to REVISION_REQUIRED
    sub_check_res = client.get(f"/api/v1/submissions/{submission_id}", headers=s_headers)
    assert sub_check_res.status_code == 200
    assert sub_check_res.json()["status"] == "REVISION_REQUIRED"

    # 5. Student creates a help issue ticket requesting more time (Level 3 escalation check)
    issue_payload = {
        "assignment_id": assignment_id,
        "submission_id": submission_id,
        "category": "EXTENSION_REQUEST",
        "description": "I need more time to purchase additional fabric."
    }
    issue_res = client.post("/api/v1/issues/", json=issue_payload, headers=s_headers)
    assert issue_res.status_code == 200
    issue_id = issue_res.json()["id"]

    # Student posts message to the thread asking for an extension -> Should trigger Level 3 escalation
    msg_payload = {
        "content": "Can I have an extension for 2 days?"
    }
    msg_res = client.post(f"/api/v1/issues/{issue_id}/messages", json=msg_payload, headers=s_headers)
    assert msg_res.status_code == 200

    # Verify ticket escalation state updated
    issue_check_res = client.get(f"/api/v1/issues/{issue_id}", headers=s_headers)
    assert issue_check_res.status_code == 200
    assert issue_check_res.json()["escalation_level"] == 3
    assert issue_check_res.json()["status"] == "ESCALATED"
