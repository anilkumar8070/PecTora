from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import logging
from typing import Dict, List, Optional
from app.models import Mission
from app.ollama import generate_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ProxyPact API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session state
sessions: Dict[str, Mission] = {}
connections: Dict[str, List[WebSocket]] = {}

@app.post("/api/mission")
async def create_mission(mission: Mission):
    session_id = "default"  # Using a single session for MVP
    sessions[session_id] = mission
    return {"status": "success", "session_id": session_id}

@app.get("/api/mission")
async def get_mission():
    session_id = "default"
    if session_id in sessions:
        return sessions[session_id]
    return {"status": "no_mission"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = "default"
    
    if session_id not in connections:
        connections[session_id] = []
    connections[session_id].append(websocket)
    
    # Send history or welcome
    await websocket.send_json({"sender": "System", "text": "Connected to ProxyPact Room.", "type": "SYSTEM"})
    
    chat_history = []
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                transcript = payload.get("text", "")
                
                # Broadcast friend message
                for conn in connections[session_id]:
                    await conn.send_json({"sender": "Friend", "text": transcript, "type": "PUBLIC"})
                
                chat_history.append({"role": "user", "content": transcript})
                
                # Retrieve mission
                mission = sessions.get(session_id)
                if not mission:
                    continue
                
                # Generate AI response
                ai_response = await generate_response(mission, chat_history)
                
                if ai_response:
                    action = ai_response.get("action", "REPLY")
                    msg = ai_response.get("message", "I cannot answer that right now.")
                    reason = ai_response.get("reason", "")
                    
                    # Privacy check: Ensure AI didn't leak private constraints
                    msg_lower = msg.lower()
                    for constraint in mission.private_constraints:
                        # Extract key terms from the constraint to check
                        words = [w.lower() for w in constraint.split() if len(w) > 3]
                        if any(w in msg_lower for w in words):
                            msg = "I must consult with the owner on this specific condition. I am escalating this."
                            action = "ESCALATE"
                            reason = "Privacy check triggered"
                            break
                            
                    chat_history.append({"role": "assistant", "content": msg})
                    
                    # Broadcast AI message
                    for conn in connections[session_id]:
                        await conn.send_json({
                            "sender": "Agent", 
                            "text": msg, 
                            "type": "PUBLIC",
                            "action": action,
                            "reason": reason
                        })
                
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        connections[session_id].remove(websocket)
