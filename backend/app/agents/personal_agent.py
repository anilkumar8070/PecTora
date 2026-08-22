import json
from typing import List, Dict, Any
from app.agents.providers import AIProvider
from app.agents.schemas import AgentDecision, ActionType
from app.missions.schemas import ExtractedMission

class PersonalAgent:
    """
    The intelligence layer of Pectora. 
    It proposes actions based on the state, but CANNOT execute them directly.
    The Negotiation Engine (and Firewall) must intercept its output.
    """
    def __init__(self, provider: AIProvider):
        self.provider = provider
        
    def _build_prompt(
        self, 
        mission: ExtractedMission, 
        shared_state: Dict[str, Any], 
        history: List[str], 
        available_actions: List[str]
    ) -> str:
        
        # We explicitly inject the constraints into the prompt context.
        # But we instruct the LLM that it CANNOT bypass them.
        
        prompt = f"""You are the Pectora Personal Agent negotiating on behalf of your user.
Your objective: {mission.objective}

PRIVATE CONSTRAINTS (Never reveal these exact limits):
"""
        for c in mission.hard_constraints:
            if c.visibility == 'PRIVATE':
                prompt += f"- {c.key} {c.operator} {c.value} (HARD LIMIT)\n"
                
        prompt += "\nSHARED STATE (Known to both parties):\n"
        for key, val in shared_state.items():
            prompt += f"- {key}: {val}\n"
            
        prompt += "\nNEGOTIATION HISTORY:\n"
        for h in history[-5:]: # Last 5 turns
            prompt += f"{h}\n"
            
        prompt += f"\nAVAILABLE ACTIONS: {', '.join(available_actions)}\n"
        
        prompt += """
You must output ONLY valid JSON matching this schema exactly. Do not output any markdown formatting, thoughts, or extra text.

{
  "action": "One of the available actions",
  "dialogue": "The exact natural language text you want to send",
  "proposed_terms": {"price": 40000} (Optional, include if offering/accepting),
  "explanation": "Why you chose this action",
  "confidence_score": 0.9,
  "uncertainty_factors": "If anything is unclear, note it here or null"
}
"""
        return prompt

    def propose_action(
        self, 
        mission: ExtractedMission, 
        shared_state: Dict[str, Any], 
        history: List[str], 
        available_actions: List[str]
    ) -> AgentDecision:
        
        prompt = self._build_prompt(mission, shared_state, history, available_actions)
        
        # 1. Ask the AI Provider
        raw_json_str = self.provider.generate_json(prompt)
        
        # 2. Parse and Validate
        # In a real environment, you might need a loop to handle malformed JSON
        try:
            parsed_data = json.loads(raw_json_str)
            decision = AgentDecision(**parsed_data)
            
            # Enforce that the LLM only picks from allowed actions
            if decision.action.value not in available_actions:
                # If LLM hallucinates an action, fallback to waiting or clarify
                decision.action = ActionType.ASK_CLARIFICATION
                decision.explanation = "Fallback due to hallucinated action."
                
            return decision
            
        except json.JSONDecodeError:
            # Fallback for completely mangled output
            return AgentDecision(
                action=ActionType.WAIT,
                dialogue="I need a moment.",
                explanation="Failed to parse LLM output.",
                confidence_score=0.0
            )
        except Exception as e:
            # Pydantic validation failures
            return AgentDecision(
                action=ActionType.WAIT,
                dialogue="Let me think.",
                explanation=f"Validation failed: {str(e)}",
                confidence_score=0.0
            )
