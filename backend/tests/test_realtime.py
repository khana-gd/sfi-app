import pytest
import time
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from fastapi import status
from app.main import app
from app.core.tickets import ticket_store

client = TestClient(app)


def get_ws_ticket(email: str) -> str:
    # 1. Login to get session JWT token
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "KanhaDevPass2026!"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # 2. Call ws-ticket endpoint
    headers = {"Authorization": f"Bearer {token}"}
    ticket_response = client.post("/api/v1/auth/ws-ticket", headers=headers)
    assert ticket_response.status_code == 200
    return ticket_response.json()["ticket"]


def test_websocket_ticket_replay():
    # 1. Obtain ticket for student 1
    ticket = get_ws_ticket("student1@kanha.local")
    
    # 2. First connection handshake succeeds
    with client.websocket_connect(f"/api/v1/chat/ws?ticket={ticket}") as ws1:
        # Handshake accepted
        pass

    # 3. Try to reuse the same ticket immediately -> Should be rejected with 1008
    with pytest.raises(Exception) as exc_info:
        with client.websocket_connect(f"/api/v1/chat/ws?ticket={ticket}") as ws2:
            pass
    # TestClient raises WebSocketDisconnect or RuntimeError when closed immediately
    assert "1008" in str(exc_info.value) or exc_info.type.__name__ in ["WebSocketDisconnect", "RuntimeError"]


def test_websocket_ticket_race_condition():
    # 1. Obtain ticket
    ticket = get_ws_ticket("student1@kanha.local")
    
    # 2. Race connection: first connection succeeds and consumes the ticket
    with client.websocket_connect(f"/api/v1/chat/ws?ticket={ticket}") as ws1:
        
        # 3. Second connection concurrently racing on the same ticket -> Must fail
        with pytest.raises(Exception) as exc_info:
            with client.websocket_connect(f"/api/v1/chat/ws?ticket={ticket}") as ws2:
                pass
        assert "1008" in str(exc_info.value) or exc_info.type.__name__ in ["WebSocketDisconnect", "RuntimeError"]


def test_websocket_ticket_expiration():
    # 1. Obtain ticket
    ticket = get_ws_ticket("student1@kanha.local")
    
    # 2. Manually expire the ticket in WSTicketStore to simulate expired ticket
    assert ticket in ticket_store._tickets
    ticket_store._tickets[ticket]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    
    # 3. Handshake should be rejected
    with pytest.raises(Exception) as exc_info:
        with client.websocket_connect(f"/api/v1/chat/ws?ticket={ticket}") as ws:
            pass
    assert "1008" in str(exc_info.value) or exc_info.type.__name__ in ["WebSocketDisconnect", "RuntimeError"]


def test_websocket_rate_limit():
    ticket = get_ws_ticket("student1@kanha.local")
    
    with client.websocket_connect(f"/api/v1/chat/ws?ticket={ticket}") as ws:
        # Send 6 messages in rapid succession (Limit is 5 per second)
        # We target student1 sending message to faculty (recipient ID is 2, since faculty profile id is 2)
        payload = {
            "type": "SEND_MESSAGE",
            "recipient_id": 2, # faculty user id is 2
            "content": "Basics review query."
        }
        
        responses = []
        for _ in range(6):
            ws.send_json(payload)
            # Sleep slightly to let the event loop process
            time.sleep(0.01)

        # Retrieve the error frame that was sent back for the 6th message
        response = ws.receive_json()
        assert response["type"] == "ERROR"
        assert "Rate limit exceeded" in response["content"]


def test_websocket_cross_boundary():
    ticket = get_ws_ticket("student1@kanha.local")
    
    with client.websocket_connect(f"/api/v1/chat/ws?ticket={ticket}") as ws:
        # Student 1 tries to send a message to Student 2 (unauthorized target)
        # student2 user id is 4
        payload = {
            "type": "SEND_MESSAGE",
            "recipient_id": 4,
            "content": "Hey fellow student!"
        }
        ws.send_json(payload)
        
        response = ws.receive_json()
        assert response["type"] == "ERROR"
        assert "boundary violation" in response["content"]


def get_token(email: str) -> str:
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "KanhaDevPass2026!"}
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_chat_history_scoping():
    student1_token = get_token("student1@kanha.local")
    student2_token = get_token("student2@kanha.local")
    
    # 1. Authorized scoping check: Student 1 requesting history with Faculty (recipient_id=2) -> 200
    res_auth = client.get(
        "/api/v1/chat/messages/2",
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert res_auth.status_code == 200
    assert isinstance(res_auth.json(), list)

    # 2. Unauthorized cross-student boundary: Student 1 requesting history with Student 2 (recipient_id=4) -> 403
    res_stud = client.get(
        "/api/v1/chat/messages/4",
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert res_stud.status_code == 403

    # 3. Unauthorized cross-faculty boundary: Student 1 requesting history with unauthorized Faculty 2 -> 403
    # First create Faculty 2 dynamically
    admin_token = get_token("admin@kanha.local")
    import uuid
    unique_email = f"fac_chat_{uuid.uuid4().hex[:6]}@kanha.local"
    reg_payload = {
        "email": unique_email,
        "password": "KanhaDevPass2026!",
        "first_name": "Prof. Chat",
        "last_name": "Test",
        "role": "FACULTY",
        "is_active": True
    }
    reg_response = client.post(
        "/api/v1/users",
        json=reg_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reg_response.status_code == 200
    fac2_user_id = reg_response.json()["id"]

    # Student 1 requests history with unauthorized Faculty 2 -> 403
    res_fac2 = client.get(
        f"/api/v1/chat/messages/{fac2_user_id}",
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert res_fac2.status_code == 403
