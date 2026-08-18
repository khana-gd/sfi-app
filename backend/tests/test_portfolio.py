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
def student2_headers():
    token = get_token("student2@kanha.local")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def faculty_headers():
    token = get_token("faculty@kanha.local")
    return {"Authorization": f"Bearer {token}"}

def test_portfolio_lifecycle_and_ownership(student1_headers, student2_headers, faculty_headers):
    # 1. Create a portfolio item as Student 1
    payload = {
        "title": "Zardozi Lehenga Draft",
        "category": "ILLUSTRATION",
        "description": "Gold stitch pattern drafting",
        "file_url": "/static/fashion_ai/concept_lehenga.jpg"
    }
    response = client.post("/api/v1/portfolio/items", json=payload, headers=student1_headers)
    assert response.status_code == 200
    item_data = response.json()
    assert item_data["title"] == "Zardozi Lehenga Draft"
    assert item_data["category"] == "ILLUSTRATION"
    item_id = item_data["id"]

    # 2. Verify Student 1 can retrieve their portfolio items
    response = client.get("/api/v1/portfolio/items", headers=student1_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert any(i["id"] == item_id for i in items)

    # 3. Verify Student 2 (unauthorized student) is blocked from retrieving Student 1's portfolio
    # In seeded DB, student1 has student profile ID 1 (user id 3)
    response = client.get("/api/v1/portfolio/items?student_id=1", headers=student2_headers)
    assert response.status_code == 403

    # 4. Verify Student 2 is blocked from deleting Student 1's portfolio item
    response = client.delete(f"/api/v1/portfolio/items/{item_id}", headers=student2_headers)
    assert response.status_code == 403

    # 5. Verify Faculty can view Student 1's portfolio items
    response = client.get("/api/v1/portfolio/items?student_id=1", headers=faculty_headers)
    assert response.status_code == 200
    faculty_items = response.json()
    assert any(i["id"] == item_id for i in faculty_items)

    # 6. Verify print/PDF export
    f_token = faculty_headers["Authorization"].split(" ")[1]
    response = client.get(f"/api/v1/portfolio/export/pdf?student_id=1&token={f_token}")
    assert response.status_code == 200
    assert "Fashion Portfolio" in response.text
    assert "Zardozi Lehenga Draft" in response.text

    # 7. Delete the item as Student 1
    response = client.delete(f"/api/v1/portfolio/items/{item_id}", headers=student1_headers)
    assert response.status_code == 200
    assert response.json()["detail"] == "Portfolio item deleted successfully."
