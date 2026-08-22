import enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class NegotiationState(str, enum.Enum):
    CREATED = "CREATED"
    READY = "READY"
    CONNECTING = "CONNECTING"
    OPENING = "OPENING"
    OFFER_RECEIVED = "OFFER_RECEIVED"
    OFFER_EVALUATION = "OFFER_EVALUATION"
    COUNTEROFFER = "COUNTEROFFER"
    CONCESSION = "CONCESSION"
    WAITING = "WAITING"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    VERIFYING = "VERIFYING"
    AGREED = "AGREED"
    REJECTED = "REJECTED"
    WALKED_AWAY = "WALKED_AWAY"
    FAILED = "FAILED"

class Offer(BaseModel):
    terms: Dict[str, Any]
    
class CounterOffer(Offer):
    pass
    
class Concession(BaseModel):
    key: str
    previous_value: Any
    new_value: Any

class NegotiationTurn(BaseModel):
    turn_number: int
    sender: str # "AGENT" or "COUNTERPARTY"
    raw_message: str
    offer: Optional[Offer] = None
    concessions: List[Concession] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LLMRecommendation(BaseModel):
    intent: str # e.g. "ACCEPT", "REJECT", "COUNTER", "CLARIFY"
    dialogue: str
    proposed_offer: Optional[Dict[str, Any]] = None
