import pytest
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.websockets import router
from app.communication.websocket_manager import manager
from app.communication.schemas import EventVisibility, EventType

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_manager():
    manager.active_connections = {}
    manager.valid_tokens = {}
    manager.session_history = {}
    yield

from starlette.websockets import WebSocketDisconnect

def test_01_invalid_token_rejected():
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/invalid_token") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "ERROR"
            websocket.receive_json()
    assert exc_info.value.code == 1008

def test_02_valid_connection_succeeds():
    token = manager.generate_token("session1", "user1")
    with client.websocket_connect(f"/ws/{token}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == EventType.PARTICIPANT_JOINED
        assert data["sender_id"] == "user1"
        assert data["visibility"] == EventVisibility.SYSTEM

def test_03_public_message_broadcast():
    token1 = manager.generate_token("sess", "u1")
    token2 = manager.generate_token("sess", "u2")
    
    with client.websocket_connect(f"/ws/{token1}") as ws1:
        # u1 receives its own join event
        ws1.receive_json()
        
        with client.websocket_connect(f"/ws/{token2}") as ws2:
            # History includes u1's join
            ws2.receive_json()
            # Then u2's join
            ws2.receive_json()
            
            # u1 also receives u2's join
            ws1.receive_json()
            
            # u1 sends public message
            ws1.send_json({"type": "MESSAGE", "visibility": "PUBLIC", "payload": {"text": "hello"}})
            
            # Both should receive it
            msg1 = ws1.receive_json()
            msg2 = ws2.receive_json()
            
            assert msg1["payload"]["text"] == "hello"
            assert msg2["payload"]["text"] == "hello"
            assert msg1["sender_id"] == "u1"
            assert msg1["visibility"] == "PUBLIC"

def test_04_private_message_filtered():
    token1 = manager.generate_token("sess_priv", "u1")
    token2 = manager.generate_token("sess_priv", "u2")
    
    with client.websocket_connect(f"/ws/{token1}") as ws1:
        ws1.receive_json() # u1 join
        
        with client.websocket_connect(f"/ws/{token2}") as ws2:
            ws2.receive_json() # u1 join from history
            ws2.receive_json() # u2 join
            ws1.receive_json() # u2 join
            
            # u1 sends private message (e.g. AGENT_THINKING)
            ws1.send_json({"type": "AGENT_THINKING", "visibility": "PRIVATE", "payload": {"thought": "my max is 42000"}})
            
            # u1 should receive it back (as an echo/confirmation)
            msg1 = ws1.receive_json()
            assert msg1["type"] == "AGENT_THINKING"
            assert msg1["payload"]["thought"] == "my max is 42000"
            
            # u2 should NOT receive it. We can test this by sending a public message right after
            # and asserting that the NEXT message u2 receives is the public one, skipping the private one.
            ws1.send_json({"type": "MESSAGE", "visibility": "PUBLIC", "payload": {"text": "ping"}})
            
            ws1.receive_json() # u1 gets ping
            msg2 = ws2.receive_json() # u2 should get ping
            
            assert msg2["type"] == "MESSAGE"
            assert msg2["payload"]["text"] == "ping"

def test_05_reconnect_gets_history():
    token1 = manager.generate_token("sess3", "u1")
    
    with client.websocket_connect(f"/ws/{token1}") as ws1:
        ws1.receive_json() # u1 join
        ws1.send_json({"type": "MESSAGE", "visibility": "PUBLIC", "payload": {"text": "test"}})
        ws1.receive_json() # receive test
    
    # Reconnect with a new token for same user
    token1_new = manager.generate_token("sess3", "u1")
    with client.websocket_connect(f"/ws/{token1_new}") as ws1_new:
        history1 = ws1_new.receive_json() # old join
        history2 = ws1_new.receive_json() # test msg
        history3 = ws1_new.receive_json() # leave event from old connection
        new_join = ws1_new.receive_json() # new join
        
        assert history2["payload"]["text"] == "test"
