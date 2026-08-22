import enum
from typing import Dict, Any
from pydantic import BaseModel, Field

class EventVisibility(str, enum.Enum):
    PUBLIC = "PUBLIC"    # Broadcast to all
    PRIVATE = "PRIVATE"  # Sent only to the owner (e.g. Agent thinking, internal constraints)
    SYSTEM = "SYSTEM"    # System-level broadcasts

class EventType(str, enum.Enum):
    SESSION_CREATED = "SESSION_CREATED"
    PARTICIPANT_JOINED = "PARTICIPANT_JOINED"
    OFFER = "OFFER"
    COUNTEROFFER = "COUNTEROFFER"
    MESSAGE = "MESSAGE"
    AGENT_THINKING = "AGENT_THINKING"
    AGENT_ACTION = "AGENT_ACTION"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    AGREEMENT = "AGREEMENT"
    NEGOTIATION_FAILED = "NEGOTIATION_FAILED"
    PARTICIPANT_LEFT = "PARTICIPANT_LEFT"
    ERROR = "ERROR"
    WEBRTC_OFFER = "WEBRTC_OFFER"
    WEBRTC_ANSWER = "WEBRTC_ANSWER"
    WEBRTC_ICE_CANDIDATE = "WEBRTC_ICE_CANDIDATE"

class WebSocketEvent(BaseModel):
    type: EventType
    visibility: EventVisibility = EventVisibility.PUBLIC
    sender_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
