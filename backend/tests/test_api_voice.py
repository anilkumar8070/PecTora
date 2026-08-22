import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.communication.websocket_manager import manager

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_manager():
    manager.active_connections = {}
    manager.valid_tokens = {}
    manager.session_history = {}
    yield

def test_voice_turn_unauthorized():
    res = client.post("/api/voice/turn", data={"token": "invalid"}, files={"audio": ("test.webm", b"audio_bytes")})
    assert res.status_code == 401

def test_voice_turn_success():
    token = manager.generate_token("sess1", "user1")
    
    res = client.post(
        "/api/voice/turn",
        data={"token": token},
        files={"audio": ("test.webm", b"audio_bytes", "audio/webm")}
    )
    
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
    
    # Check that it streamed the mock TTS audio chunks
    content = b""
    for chunk in res.iter_bytes():
        content += chunk
        
    assert content == b"mock_audio_bytes"
