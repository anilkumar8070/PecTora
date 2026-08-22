from pydantic import ValidationError
from typing import Tuple, Optional, Dict, Any
from app.missions.schemas import ExtractedMission
import json

class MissionParser:
    """
    Simulates or interfaces with the LLM to extract JSON from text.
    In production, this delegates to an LLM provider (Ollama) with strict JSON mode.
    """
    def __init__(self, llm_client=None):
        self.llm = llm_client
        
    def parse_mock(self, mock_llm_json: str) -> dict:
        """For testing deterministic validation without waiting for an LLM."""
        return json.loads(mock_llm_json)
        
    async def extract_from_text(self, text: str) -> dict:
        if self.llm:
            # Call actual LLM
            pass
        return {}

class MissionValidator:
    """
    Deterministically validates the LLM's extracted structure.
    Ensures constraints make sense and no critical bounds are invented.
    """
    def validate(self, raw_data: dict) -> Tuple[Optional[ExtractedMission], list]:
        try:
            mission = ExtractedMission(**raw_data)
            clarifications_needed = []
            
            # Add LLM-identified missing info
            clarifications_needed.extend(mission.missing_critical_info)
            
            # Deterministic Check: If the objective implies a purchase/sale, a hard limit MUST exist
            obj_lower = mission.objective.lower()
            if any(word in obj_lower for word in ['buy', 'purchase', 'negotiate', 'rent', 'kharidna', 'khareed']):
                has_price_limit = any(
                    (c.key in ['price', 'budget', 'rent']) and (c.operator in ['<=', '<', '==', 'max']) 
                    for c in mission.hard_constraints
                )
                if not has_price_limit:
                    if "maximum price" not in clarifications_needed:
                        clarifications_needed.append("maximum price")
            
            if any(word in obj_lower for word in ['sell', 'bechna']):
                has_min_price = any(
                    (c.key in ['price']) and (c.operator in ['>=', '>', '==', 'min'])
                    for c in mission.hard_constraints
                )
                if not has_min_price:
                    if "minimum selling price" not in clarifications_needed:
                        clarifications_needed.append("minimum selling price")

            return mission, clarifications_needed
        except ValidationError as e:
            return None, [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]

class ClarificationGenerator:
    """
    Generates deterministic or LLM-assisted clarification questions.
    """
    def generate(self, missing_info: list) -> str:
        if not missing_info:
            return "Mission fully understood. Ready to proceed."
        
        missing_str = ", ".join(missing_info)
        return f"I need a bit more clarity. You did not specify the {missing_str}. Please provide this so I do not exceed your limits."
