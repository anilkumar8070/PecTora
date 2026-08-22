from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.missions.schemas import ExtractedMission, ConstraintSchema
from app.negotiation.schemas import NegotiationState
from app.voice.processor import VoiceProcessor
from app.voice.providers import LocalSpeechToTextProvider # Or Mock
import logging

logger = logging.getLogger(__name__)

class HumanApprovalRequest(BaseModel):
    what_happened: str
    current_offer: Dict[str, Any]
    new_condition: str
    reason: str
    agent_recommendation: str

class HumanApprovalEngine:
    """
    Handles pauses in negotiation when an un-delegated condition is introduced.
    Allows the human to MODIFY the mission by adding specific constraints dynamically,
    without overwriting the original hard constraints.
    """
    def __init__(self, voice_processor: VoiceProcessor = None):
        self.voice_processor = voice_processor
        
    def generate_approval_request(self, incoming_offer: Dict[str, Any], unknown_condition: str) -> HumanApprovalRequest:
        return HumanApprovalRequest(
            what_happened="The other party introduced a new term not covered by your instructions.",
            current_offer=incoming_offer,
            new_condition=unknown_condition,
            reason="I am not authorized to accept or negotiate this condition without explicit permission.",
            agent_recommendation="I recommend we accept if the timeline is reasonable, or counter with a stricter deadline."
        )

    def process_modification(self, mission: ExtractedMission, new_instruction_text: str) -> ExtractedMission:
        """
        Takes the human's spoken modification (e.g. "Delivery should be maximum 7 days"),
        and deterministically applies it to the mission.
        """
        # In a real implementation, we pass the instruction back through MissionParser
        # For determinism and safety, we never touch existing constraints.
        
        # Simplified Mock Logic:
        instruction_lower = new_instruction_text.lower()
        if "delivery" in instruction_lower and "7" in instruction_lower:
            new_constraint = ConstraintSchema(
                key="delivery_days",
                operator="<=",
                value=7,
                visibility="PRIVATE",
                type="HARD"
            )
            mission.hard_constraints.append(new_constraint)
            logger.info(f"Added new constraint via human modification: {new_constraint}")
            
            # We also grant permission to negotiate this
            # (In reality, we'd append to mission.permissions)
            
        return mission
