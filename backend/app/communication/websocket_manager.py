from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional, Tuple
import logging
from app.communication.schemas import WebSocketEvent, EventVisibility, EventType
import uuid

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # session_id -> { participant_id: WebSocket }
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # token -> {"session_id": session_id, "participant_id": participant_id}
        self.valid_tokens: Dict[str, Dict[str, str]] = {}
        # Simple history persistence for reconnects (session_id -> list of events)
        self.session_history: Dict[str, list] = {}

    def create_session(self, session_id: str):
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
            self.session_history[session_id] = []

    def generate_token(self, session_id: str, participant_id: str) -> str:
        token = str(uuid.uuid4())
        self.valid_tokens[token] = {"session_id": session_id, "participant_id": participant_id}
        return token

    async def connect(self, websocket: WebSocket, token: str) -> Tuple[Optional[str], Optional[str]]:
        await websocket.accept()
        
        if token not in self.valid_tokens:
            await websocket.send_json({"type": EventType.ERROR, "payload": {"message": "Invalid authentication token"}})
            await websocket.close(code=1008)
            return None, None
            
        auth = self.valid_tokens[token]
        session_id = auth["session_id"]
        participant_id = auth["participant_id"]
        
        self.create_session(session_id)
        self.active_connections[session_id][participant_id] = websocket
        
        # Send history on connect (only public/system or their own private events)
        for event_dict in self.session_history[session_id]:
            if event_dict["visibility"] == EventVisibility.PRIVATE.value and event_dict["sender_id"] != participant_id:
                continue
            await websocket.send_json(event_dict)
            
        return session_id, participant_id

    def disconnect(self, session_id: str, participant_id: str):
        if session_id in self.active_connections:
            if participant_id in self.active_connections[session_id]:
                del self.active_connections[session_id][participant_id]

    async def broadcast(self, session_id: str, event: WebSocketEvent):
        """
        Sends the event to participants in the session.
        Applies visibility rules.
        """
        if session_id not in self.active_connections:
            return
            
        event_dict = event.model_dump()
        self.session_history[session_id].append(event_dict)
            
        dead_connections = []
        
        for p_id, connection in self.active_connections[session_id].items():
            # PRIVATE filter: Only send if it's the sender
            if event.visibility == EventVisibility.PRIVATE and event.sender_id != p_id:
                continue
                
            try:
                await connection.send_json(event_dict)
            except RuntimeError:
                dead_connections.append(p_id)
            except Exception as e:
                logger.error(f"Failed to send message to {p_id}: {e}")
                dead_connections.append(p_id)
                
        for p_id in dead_connections:
            self.disconnect(session_id, p_id)

manager = ConnectionManager()
