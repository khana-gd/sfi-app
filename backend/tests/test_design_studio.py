import pytest
from fastapi.testclient import TestClient
from io import BytesIO

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

def test_design_studio_project_and_moodboard_flow(auth_headers):
    # 1. Student creates a design project
    proj_payload = {
        "name": "Winter Bridal Collection 2026",
        "inspiration_source": "Mughal architecture shapes",
        "fabric_notes": "Velvet, Raw Silk",
        "color_palette": "Navy Blue, Gold, Ivory"
    }
    res = client.post("/api/v1/design-studio/projects", json=proj_payload, headers=auth_headers)
    assert res.status_code == 200
    proj_data = res.json()
    assert proj_data["name"] == "Winter Bridal Collection 2026"
    proj_id = proj_data["id"]
    
    # 2. Student lists their projects
    list_res = client.get("/api/v1/design-studio/projects", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(p["id"] == proj_id for p in list_res.json())
    
    # 3. Student creates a moodboard
    mb_payload = {
        "project_id": proj_id,
        "name": "Moodboard 1: Embroidery & Layouts"
    }
    mb_res = client.post("/api/v1/design-studio/moodboards", json=mb_payload, headers=auth_headers)
    assert mb_res.status_code == 200
    mb_data = mb_res.json()
    assert mb_data["name"] == "Moodboard 1: Embroidery & Layouts"
    mb_id = mb_data["id"]
    
    # 3.5 Student lists moodboards of the project
    mb_list_res = client.get(f"/api/v1/design-studio/projects/{proj_id}/moodboards", headers=auth_headers)
    assert mb_list_res.status_code == 200
    assert any(m["id"] == mb_id for m in mb_list_res.json())
    
    # 4. Student adds a third-party reference image item with valid attribution
    item_payload = {
        "item_type": "REFERENCE_IMAGE",
        "file_url": "/static/references/img1.jpg",
        "caption": "Mughal dome inspiration",
        "source_url": "https://wikipedia.org/wiki/Mughal_architecture",
        "source_title": "Wikipedia Mughal Architecture page",
        "is_ai_generated": False
    }
    item_res = client.post(f"/api/v1/design-studio/moodboards/{mb_id}/items", json=item_payload, headers=auth_headers)
    assert item_res.status_code == 200
    item_data = item_res.json()
    assert item_data["item_type"] == "REFERENCE_IMAGE"
    assert item_data["source_title"] == "Wikipedia Mughal Architecture page"
    
    # 5. Adding third-party reference image WITHOUT attribution must fail with 400 Bad Request
    invalid_item_payload = {
        "item_type": "REFERENCE_IMAGE",
        "file_url": "/static/references/img1.jpg",
        "caption": "Mughal dome inspiration",
        "is_ai_generated": False
    }
    invalid_res = client.post(f"/api/v1/design-studio/moodboards/{mb_id}/items", json=invalid_item_payload, headers=auth_headers)
    assert invalid_res.status_code == 400
    assert "attribution" in invalid_res.json()["detail"].lower()

def test_design_studio_ownership_boundary(auth_headers):
    # Student 2 (Zara Khan) token
    s2_token = get_token("student2@kanha.local")
    s2_headers = {"Authorization": f"Bearer {s2_token}"}
    
    # 1. Student 2 creates a design project and moodboard
    proj_res = client.post(
        "/api/v1/design-studio/projects", 
        json={"name": "Zara's Private Collection"}, 
        headers=s2_headers
    )
    assert proj_res.status_code == 200
    proj_id = proj_res.json()["id"]
    
    mb_res = client.post(
        "/api/v1/design-studio/moodboards", 
        json={"project_id": proj_id, "name": "Zara Moodboard"}, 
        headers=s2_headers
    )
    assert mb_res.status_code == 200
    mb_id = mb_res.json()["id"]
    
    # 2. Student 1 (unauthorized) tries to retrieve Student 2's project details -> Should be 403
    s1_get_proj_res = client.get(f"/api/v1/design-studio/projects/{proj_id}", headers=auth_headers)
    assert s1_get_proj_res.status_code == 403
    
    # 3. Student 1 (unauthorized) tries to retrieve Student 2's moodboard details -> Should be 403
    s1_get_mb_res = client.get(f"/api/v1/design-studio/moodboards/{mb_id}", headers=auth_headers)
    assert s1_get_mb_res.status_code == 403
    
    # 4. Student 1 (unauthorized) tries to add an item to Student 2's moodboard -> Should be 403
    s1_add_item_res = client.post(
        f"/api/v1/design-studio/moodboards/{mb_id}/items",
        json={"item_type": "AI_CONCEPT", "file_url": "/static/test.png"},
        headers=auth_headers
    )
    assert s1_add_item_res.status_code == 403

def test_text_to_design_generation(auth_headers):
    # 1. Verify text-to-design mock works and returns status 200
    payload = {
        "silhouette": "Lehenga",
        "fabric": "Velvet",
        "colors": "Navy blue and gold",
        "embroidery": "Zardozi motifs"
    }
    res = client.post("/api/v1/design-studio/concept", data=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "/static/fashion_ai/concept_lehenga.jpg" in data["file_url"]
    assert data["is_ai_generated"] is True

def test_sketch_analysis_multimodal(auth_headers):
    # 1. Verify sketch analysis upload runs and returns suggestions
    fake_file_content = b"fake pencil sketch image contents"
    file_payload = {"file": ("sketch.jpg", BytesIO(fake_file_content), "image/jpeg")}
    
    res = client.post(
        "/api/v1/design-studio/sketch/analyze",
        files=file_payload,
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert "Flared Kalidar Gown" in data["silhouette"]
    assert "Zardozi hand-embroidery" in data["embroidery"]
    assert "analysis" in data
