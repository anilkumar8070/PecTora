from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Pectora-backend"}

def test_websocket_auth_rejection():
    # WebSocket should reject connection if no valid token is provided
    with client.websocket_connect("/ws/session") as websocket:
        websocket.send_text("Hello Pectora")
        data = websocket.receive_json()
        assert data["type"] == "ERROR"
        assert "Invalid authentication token" in data["payload"]["message"]
