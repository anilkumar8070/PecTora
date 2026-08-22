import enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class ActionType(str, enum.Enum):
    OFFER = "OFFER"
    COUNTER = "COUNTER"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    ASK_CLARIFICATION = "ASK_CLARIFICATION"
    REQUEST_HUMAN = "REQUEST_HUMAN"
    WALK_AWAY = "WALK_AWAY"
    WAIT = "WAIT"

class AgentDecision(BaseModel):
    action: ActionType = Field(description="The selected action type.")
    dialogue: str = Field(description="The natural language dialogue to send to the counterparty.")
    proposed_terms: Optional[Dict[str, Any]] = Field(None, description="The specific terms if action is OFFER, COUNTER, or ACCEPT.")
    explanation: str = Field(description="Concise explanation for why this action was chosen.")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in the decision (0.0 to 1.0).")
    uncertainty_factors: Optional[str] = Field(None, description="Factors causing uncertainty, if any.")
