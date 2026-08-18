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
def auth_headers():
    token = get_token("student1@kanha.local")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def faculty_headers():
    token = get_token("faculty@kanha.local")
    return {"Authorization": f"Bearer {token}"}

def test_research_grounded_query_mughal(auth_headers):
    # Test Mughal query lookup
    payload = {"query": "Tell me about Mughal costumes and zardozi borders"}
    res = client.post("/api/v1/research/query", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "mughal" in data["query"].lower()
    assert "pietra dura" in data["grounded_text"].lower()
    assert len(data["citations"]) == 2
    assert data["citations"][0]["index"] == 1
    assert "National Museum" in data["citations"][0]["title"]

def test_research_grounded_query_draping(auth_headers):
    # Test draping query lookup
    payload = {"query": "What are traditional draping techniques?"}
    res = client.post("/api/v1/research/query", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "crinoline" in data["grounded_text"].lower()
    assert len(data["citations"]) == 2
    assert "Fashion Institute" in data["citations"][0]["title"]

def test_google_docs_export(auth_headers):
    # Test export to Google Docs mock service
    payload = {
        "title": "Mughal Embroidery Notes",
        "content_markdown": "### Introduction\nZardozi is a gold embroidery..."
    }
    res = client.post("/api/v1/google/docs/export", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "http://localhost:8000/static/google_docs/" in data["google_doc_url"]

def test_google_calendar_sync_milestone(faculty_headers):
    # Sync milestone manual trigger
    res = client.post("/api/v1/google/calendar/sync?assignment_id=1", headers=faculty_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "event_id" in data

def test_google_drive_attachment_streaming(faculty_headers, auth_headers):
    # 1. Faculty creates a new assignment targeted to Student 1 (Aarav Mehta, profile ID 1) with drive-file-1
    payload = {
        "title": "Mughal Costume Practice",
        "description": "Practice sketch guidelines.",
        "deadline": "2026-08-25T12:00:00Z",
        "priority": "HIGH",
        "category": "Illustration",
        "student_ids": [1],
        "drive_file_id": "drive-file-1",
        "drive_file_name": "SFI Mughal Costume & Architecture Guidelines.pdf",
        "drive_file_url": "https://drive.google.com/open?id=drive-file-1"
    }
    f_res = client.post("/api/v1/assignments/", json=payload, headers=faculty_headers)
    assert f_res.status_code == 200

    # 2. Student 1 streams it successfully
    res = client.get("/api/v1/google/drive/stream/drive-file-1", headers=auth_headers)
    assert res.status_code == 200
    assert b"Mughal Costumes Study Guide" in res.content
    assert "attachment" in res.headers["Content-Disposition"]

def test_google_drive_attachment_unauthorized_block(faculty_headers):
    # 1. Faculty creates a new assignment targeted only to Student 2 (Zara Khan, profile ID 2) with drive-file-2
    payload = {
        "title": "Private Study Session",
        "description": "Confidential guide.",
        "deadline": "2026-08-25T12:00:00Z",
        "priority": "LOW",
        "category": "Illustration",
        "student_ids": [2],
        "drive_file_id": "drive-file-2",
        "drive_file_name": "SFI Surface Draping & Cowl Neck Patterns.pdf",
        "drive_file_url": "https://drive.google.com/open?id=drive-file-2"
    }
    f_res = client.post("/api/v1/assignments/", json=payload, headers=faculty_headers)
    assert f_res.status_code == 200
    
    # 2. Student 2 (authorized) tries to stream the attachment
    s2_token = get_token("student2@kanha.local")
    s2_res = client.get("/api/v1/google/drive/stream/private-drive-file-2" if False else "/api/v1/google/drive/stream/drive-file-2", headers={"Authorization": f"Bearer {s2_token}"})
    assert s2_res.status_code == 200
    assert b"Draping and Cowl Construction" in s2_res.content
    
    # 3. Student 1 (unauthorized) tries to stream the attachment -> Should be 403
    s1_token = get_token("student1@kanha.local")
    s1_res = client.get("/api/v1/google/drive/stream/drive-file-2", headers={"Authorization": f"Bearer {s1_token}"})
    assert s1_res.status_code == 403

def test_research_query_rate_limiter():
    # Make a unique user to avoid triggering rate limit from other tests
    import uuid
    unique_email = f"rate_student_{uuid.uuid4().hex[:6]}@kanha.local"
    admin_token = get_token("admin@kanha.local")
    reg_res = client.post(
        "/api/v1/users/",
        json={
            "email": unique_email,
            "password": "KanhaDevPass2026!",
            "first_name": "RateLimit",
            "last_name": "Test",
            "role": "STUDENT",
            "is_active": True
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reg_res.status_code == 200
    
    token = get_token(unique_email)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make 5 queries
    for _ in range(5):
        res = client.post("/api/v1/research/query", json={"query": "mughal"}, headers=headers)
        assert res.status_code == 200
        
    # The 6th must return 429
    res = client.post("/api/v1/research/query", json={"query": "mughal"}, headers=headers)
    assert res.status_code == 429
    assert "Rate limit exceeded" in res.json()["detail"]

