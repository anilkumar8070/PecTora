import pytest
from fastapi.testclient import TestClient
from app.api.websockets import router
from app.communication.websocket_manager import manager
from fastapi import FastAPI
import uuid

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_manager():
    manager.active_connections = {}
    manager.valid_tokens = {}
    manager.session_history = {}
    yield

def test_webrtc_signaling_flow():
    # Simulate Browser A and Browser B in the same session
    session_id = "webrtc_session"
    tokenA = manager.generate_token(session_id, "browser_a")
    tokenB = manager.generate_token(session_id, "browser_b")

    with client.websocket_connect(f"/ws/{tokenA}") as wsA, \
         client.websocket_connect(f"/ws/{tokenB}") as wsB:
        
        # Drain initial join events
        wsA.receive_json() # A's join
        wsB.receive_json() # A's join (from history)
        wsB.receive_json() # B's join
        wsA.receive_json() # B's join

        # Browser A sends Offer
        offer_payload = {"sdp": {"type": "offer", "sdp": "v=0\r\n..."}}
        wsA.send_json({
            "type": "WEBRTC_OFFER",
            "visibility": "PUBLIC",
            "payload": offer_payload
        })

        # Browser B receives Offer
        msgB1 = wsB.receive_json()
        assert msgB1["type"] == "WEBRTC_OFFER"
        assert msgB1["sender_id"] == "browser_a"
        assert msgB1["payload"]["sdp"]["type"] == "offer"

        # Browser B sends Answer
        answer_payload = {"sdp": {"type": "answer", "sdp": "v=0\r\n..."}}
        wsB.send_json({
            "type": "WEBRTC_ANSWER",
            "visibility": "PUBLIC",
            "payload": answer_payload
        })

        # Browser A receives Answer
        msgA1 = wsA.receive_json() # B's answer is broadcast back to session (including A)
        
        # Drain self-broadcast if needed, depending on how you read it
        if msgA1["sender_id"] == "browser_a": 
            msgA1 = wsA.receive_json()

        assert msgA1["type"] == "WEBRTC_ANSWER"
        assert msgA1["sender_id"] == "browser_b"

        # Browser A sends ICE Candidate
        ice_payload = {"candidate": {"candidate": "candidate:1 1 UDP 2130706431", "sdpMid": "0", "sdpMLineIndex": 0}}
        wsA.send_json({
            "type": "WEBRTC_ICE_CANDIDATE",
            "visibility": "PUBLIC",
            "payload": ice_payload
        })

        # Browser B receives ICE Candidate
        msgB2 = wsB.receive_json()
        if msgB2["sender_id"] == "browser_b":
            msgB2 = wsB.receive_json()
            
        assert msgB2["type"] == "WEBRTC_ICE_CANDIDATE"
        assert msgB2["payload"]["candidate"]["sdpMid"] == "0"
