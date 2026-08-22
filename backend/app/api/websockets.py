from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.communication.websocket_manager import manager
from app.communication.schemas import WebSocketEvent, EventType, EventVisibility
import json

router = APIRouter()

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    session_id, participant_id = await manager.connect(websocket, token)
    if not session_id:
        return
        
    try:
        # Broadcast join event
        join_event = WebSocketEvent(
            type=EventType.PARTICIPANT_JOINED,
            visibility=EventVisibility.SYSTEM,
            sender_id=participant_id,
            payload={"message": f"{participant_id} joined"}
        )
        await manager.broadcast(session_id, join_event)
        
        while True:
            # Receive data
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                
                # Client sends generic message, we construct the event
                event_type = payload.get("type", EventType.MESSAGE)
                visibility = payload.get("visibility", EventVisibility.PUBLIC)
                
                event = WebSocketEvent(
                    type=event_type,
                    visibility=visibility,
                    sender_id=participant_id,
                    payload=payload.get("payload", {})
                )
                
                # Broadcast back to session
                await manager.broadcast(session_id, event)
                
            except json.JSONDecodeError:
                error_event = WebSocketEvent(
                    type=EventType.ERROR,
                    visibility=EventVisibility.PRIVATE,
                    sender_id=participant_id,
                    payload={"message": "Invalid JSON"}
                )
                await manager.broadcast(session_id, error_event)

    except WebSocketDisconnect:
        manager.disconnect(session_id, participant_id)
        leave_event = WebSocketEvent(
            type=EventType.PARTICIPANT_LEFT,
            visibility=EventVisibility.SYSTEM,
            sender_id=participant_id,
            payload={"message": f"{participant_id} left"}
        )
        await manager.broadcast(session_id, leave_event)
