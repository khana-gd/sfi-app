import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import httpx
from app.main import app
from app.core.config import settings

client = TestClient(app)

def get_token(email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "KanhaDevPass2026!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def mock_openrouter_setup():
    orig_key = settings.OPENROUTER_API_KEY
    orig_model = settings.OPENROUTER_MODEL
    
    settings.OPENROUTER_API_KEY = "test_openrouter_api_key_valid_123"
    settings.OPENROUTER_MODEL = "test-model-value"
    
    yield
    
    settings.OPENROUTER_API_KEY = orig_key
    settings.OPENROUTER_MODEL = orig_model

def test_openrouter_semantic_distress_detection_yes(mock_openrouter_setup):
    token = get_token("student1@kanha.local")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Custom mock function to intercept only OpenRouter
    original_post = httpx.Client.post
    def mock_post(self, url, *args, **kwargs):
        if "openrouter.ai" in str(url):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "YES"
                        }
                    }
                ]
            }
            return mock_response
        return original_post(self, url, *args, **kwargs)
        
    with patch("httpx.Client.post", new=mock_post):
        payload = {
            "category": "INSTRUCTION_HELP",
            "description": "Please help me, I am in high distress.",
            "assignment_id": 1
        }
        
        response = client.post("/api/v1/issues/", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["escalation_level"] == 3
        assert data["status"] == "ESCALATED"

def test_openrouter_normal_mentor_response(mock_openrouter_setup):
    token = get_token("student1@kanha.local")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Custom mock function to intercept OpenRouter with sequential responses
    original_post = httpx.Client.post
    
    # Call 1 & 2 (distress check): NO
    # Call 3 (response generation): Custom SFI OpenRouter Mentor Response Content.
    responses_list = [
        {"choices": [{"message": {"content": "NO"}}]},
        {"choices": [{"message": {"content": "NO"}}]},
        {"choices": [{"message": {"content": "Custom SFI OpenRouter Mentor Response Content."}}]}
    ]
    response_idx = 0
    
    def mock_post(self, url, *args, **kwargs):
        nonlocal response_idx
        if "openrouter.ai" in str(url):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = responses_list[response_idx]
            response_idx += 1
            return mock_response
        return original_post(self, url, *args, **kwargs)
        
    with patch("httpx.Client.post", new=mock_post):
        payload = {
            "category": "ASSIGNMENT_HELP",
            "description": "Design concept questions.",
            "assignment_id": 1
        }
        
        response = client.post("/api/v1/issues/", json=payload, headers=headers)
        assert response.status_code == 200
        issue_data = response.json()
        
        detail_res = client.get(f"/api/v1/issues/{issue_data['id']}", headers=headers)
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert len(detail_data["messages"]) == 2
        assert detail_data["messages"][1]["content"] == "Custom SFI OpenRouter Mentor Response Content."

def test_openrouter_copilot_draft_generation(mock_openrouter_setup):
    student_token = get_token("student1@kanha.local")
    faculty_token = get_token("faculty@kanha.local")
    
    original_post = httpx.Client.post
    
    # Calls for creating issues (distress NO, distress NO, mentor response)
    issue_responses = [
        {"choices": [{"message": {"content": "NO"}}]},
        {"choices": [{"message": {"content": "NO"}}]},
        {"choices": [{"message": {"content": "Mentor feedback."}}]}
    ]
    create_idx = 0
    
    # Call for draft generation
    draft_response = {"choices": [{"message": {"content": "OpenRouter Co-Pilot Draft: Review layout details."}}]}
    
    def mock_post(self, url, *args, **kwargs):
        nonlocal create_idx
        if "openrouter.ai" in str(url):
            mock_response = MagicMock()
            mock_response.status_code = 200
            if create_idx < len(issue_responses):
                mock_response.json.return_value = issue_responses[create_idx]
                create_idx += 1
            else:
                mock_response.json.return_value = draft_response
            return mock_response
        return original_post(self, url, *args, **kwargs)
        
    with patch("httpx.Client.post", new=mock_post):
        payload = {
            "category": "ASSIGNMENT_HELP",
            "description": "Ornaments layout query.",
            "assignment_id": 1
        }
        create_res = client.post("/api/v1/issues/", json=payload, headers={"Authorization": f"Bearer {student_token}"})
        assert create_res.status_code == 200
        issue_id = create_res.json()["id"]

        # Student escalates
        client.post(f"/api/v1/issues/{issue_id}/escalate", headers={"Authorization": f"Bearer {student_token}"})

        # Faculty requests draft
        draft_res = client.get(f"/api/v1/issues/{issue_id}/draft", headers={"Authorization": f"Bearer {faculty_token}"})
        assert draft_res.status_code == 200
        assert draft_res.json()["draft"] == "OpenRouter Co-Pilot Draft: Review layout details."
