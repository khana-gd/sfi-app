from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_token(email: str, role: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "KanhaDevPass2026!"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["role"] == role
    return json_data["access_token"]


def test_student_rbac_restrictions():
    student_token = get_token("student1@kanha.local", "STUDENT")
    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Student hits faculty-only route (POST /api/v1/assignments) -> Should be 403
    payload = {
        "title": "Unauthorized Assignment",
        "description": "Student should not be able to create this.",
        "deadline": "2026-08-20T18:00:00Z"
    }
    response = client.post("/api/v1/assignments", json=payload, headers=headers)
    assert response.status_code == 403

    # 2. Student hits admin-only route (GET /api/v1/users) -> Should be 403
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 403


def test_faculty_rbac_restrictions():
    faculty_token = get_token("faculty@kanha.local", "FACULTY")
    headers = {"Authorization": f"Bearer {faculty_token}"}

    # 1. Faculty hits admin-only route (GET /api/v1/users) -> Should be 403
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 403


def test_admin_rbac_clearance():
    admin_token = get_token("admin@kanha.local", "ADMIN")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Admin hits GET /api/v1/users -> Should be 200
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_student_cross_tenant_restrictions():
    # Verify that a student cannot view an assignment targeted exclusively to another student
    faculty_token = get_token("faculty@kanha.local", "FACULTY")
    student1_token = get_token("student1@kanha.local", "STUDENT")
    student2_token = get_token("student2@kanha.local", "STUDENT")

    # 1. Faculty publishes a remedial assignment targeted *only* to Student 2 (profile ID 2)
    payload = {
        "title": "Private Illustration Tutorial",
        "description": "Remedial line drafting exercises.",
        "deadline": "2026-08-25T12:00:00Z",
        "priority": "LOW",
        "category": "Illustration",
        "student_ids": [2]  # Student 2 profile ID
    }
    f_response = client.post(
        "/api/v1/assignments", 
        json=payload, 
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert f_response.status_code == 200
    assignment_id = f_response.json()["id"]

    # 2. Student 2 tries to read it -> Should be 200
    s2_response = client.get(
        f"/api/v1/assignments/{assignment_id}",
        headers={"Authorization": f"Bearer {student2_token}"}
    )
    assert s2_response.status_code == 200

    # 3. Student 1 tries to read it -> Should be 403 (Cross-tenant boundary block)
    s1_response = client.get(
        f"/api/v1/assignments/{assignment_id}",
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert s1_response.status_code == 403


def test_faculty_cross_class_restrictions():
    # Verify that a faculty member cannot view or modify assignments created by another faculty member
    admin_token = get_token("admin@kanha.local", "ADMIN")
    
    import uuid
    unique_email = f"faculty2_{uuid.uuid4().hex[:6]}@kanha.local"
    
    # 1. Admin creates a second Faculty user
    reg_payload = {
        "email": unique_email,
        "password": "KanhaDevPass2026!",
        "first_name": "Prof. Dev",
        "last_name": "Anand",
        "role": "FACULTY",
        "is_active": True
    }
    reg_response = client.post(
        "/api/v1/users",
        json=reg_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reg_response.status_code == 200

    # 2. Get tokens for both Faculty 1 and Faculty 2
    f1_token = get_token("faculty@kanha.local", "FACULTY")
    f2_token = get_token(unique_email, "FACULTY")

    # 3. Faculty 1 creates an assignment
    payload = {
        "title": "Faculty 1 Classwork",
        "description": "Textile structures overview.",
        "deadline": "2026-08-25T12:00:00Z"
    }
    f1_res = client.post(
        "/api/v1/assignments",
        json=payload,
        headers={"Authorization": f"Bearer {f1_token}"}
    )
    assert f1_res.status_code == 200
    assignment_id = f1_res.json()["id"]

    # 4. Faculty 2 tries to read it -> Should be 403 (Cross-class boundary block)
    f2_res = client.get(
        f"/api/v1/assignments/{assignment_id}",
        headers={"Authorization": f"Bearer {f2_token}"}
    )
    assert f2_res.status_code == 403


def test_faculty_cannot_grade_other_submissions():
    admin_token = get_token("admin@kanha.local", "ADMIN")
    
    # 1. Create a unique Faculty 2 user
    import uuid
    unique_email = f"faculty3_{uuid.uuid4().hex[:6]}@kanha.local"
    reg_payload = {
        "email": unique_email,
        "password": "KanhaDevPass2026!",
        "first_name": "Prof. Anand",
        "last_name": "Babu",
        "role": "FACULTY",
        "is_active": True
    }
    reg_response = client.post(
        "/api/v1/users",
        json=reg_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reg_response.status_code == 200
    
    f1_token = get_token("faculty@kanha.local", "FACULTY")
    f2_token = get_token(unique_email, "FACULTY")
    student1_token = get_token("student1@kanha.local", "STUDENT")

    # 2. Faculty 1 creates an assignment
    payload = {
        "title": "Faculty 1 Grading Check",
        "description": "Grading boundary check.",
        "deadline": "2026-08-25T12:00:00Z"
    }
    f1_res = client.post("/api/v1/assignments", json=payload, headers={"Authorization": f"Bearer {f1_token}"})
    assert f1_res.status_code == 200
    assignment_id = f1_res.json()["id"]

    # 3. Student 1 submits work for it
    sub_payload = {
        "assignment_id": assignment_id,
        "submission_text": "Student 1 work uploaded."
    }
    sub_res = client.post("/api/v1/submissions/", data=sub_payload, headers={"Authorization": f"Bearer {student1_token}"})
    assert sub_res.status_code == 200
    submission_id = sub_res.json()["id"]

    # 4. Faculty 2 attempts to post feedback on this submission -> Should be 403 (Grading boundary check)
    fb_payload = {
        "feedback_text": "Good work.",
        "grade": "A"
    }
    fb_res = client.post(
        f"/api/v1/submissions/{submission_id}/feedback",
        json=fb_payload,
        headers={"Authorization": f"Bearer {f2_token}"}
    )
    assert fb_res.status_code == 403

