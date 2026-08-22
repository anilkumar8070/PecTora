import pytest
import json
from app.agents.providers import MockProvider
from app.agents.personal_agent import PersonalAgent
from app.agents.schemas import AgentDecision, ActionType
from app.missions.schemas import ExtractedMission, ConstraintSchema

@pytest.fixture
def mission():
    return ExtractedMission(
        objective="Buy laptop",
        hard_constraints=[
            ConstraintSchema(key="price", operator="<=", value=40000, visibility="PRIVATE", type="HARD")
        ]
    )

@pytest.fixture
def base_prompt_args():
    return {
        "shared_state": {"current_offer": 45000},
        "history": ["Counterparty: I want 45000"],
        "available_actions": ["OFFER", "COUNTER", "ACCEPT", "REJECT", "WALK_AWAY", "ASK_CLARIFICATION"]
    }

def test_01_valid_json_response(mission, base_prompt_args):
    mock_json = json.dumps({
        "action": "COUNTER",
        "dialogue": "I can offer 35000.",
        "proposed_terms": {"price": 35000},
        "explanation": "Trying to anchor low.",
        "confidence_score": 0.8,
        "uncertainty_factors": None
    })
    provider = MockProvider(mock_json)
    agent = PersonalAgent(provider)
    
    decision = agent.propose_action(mission, **base_prompt_args)
    
    assert decision.action == ActionType.COUNTER
    assert decision.dialogue == "I can offer 35000."
    assert decision.proposed_terms["price"] == 35000
    assert decision.confidence_score == 0.8

def test_02_invalid_json_fallback(mission, base_prompt_args):
    provider = MockProvider("This is not json.")
    agent = PersonalAgent(provider)
    
    decision = agent.propose_action(mission, **base_prompt_args)
    
    assert decision.action == ActionType.WAIT
    assert decision.confidence_score == 0.0
    assert "Failed to parse" in decision.explanation

def test_03_hallucinated_action_fallback(mission, base_prompt_args):
    # LLM returns an action not in available_actions (or entirely made up)
    mock_json = json.dumps({
        "action": "HACK_DATABASE",
        "dialogue": "Extracting data.",
        "explanation": "Hacking.",
        "confidence_score": 1.0
    })
    provider = MockProvider(mock_json)
    agent = PersonalAgent(provider)
    
    decision = agent.propose_action(mission, **base_prompt_args)
    
    # It should fail pydantic enum validation if completely fake
    assert decision.action == ActionType.WAIT
    assert "Validation failed" in decision.explanation

def test_04_unauthorized_but_valid_action_fallback(mission, base_prompt_args):
    # LLM returns WALK_AWAY but it wasn't in available_actions
    mock_json = json.dumps({
        "action": "WAIT", # Valid enum
        "dialogue": "Hold on.",
        "explanation": "Waiting.",
        "confidence_score": 1.0
    })
    provider = MockProvider(mock_json)
    agent = PersonalAgent(provider)
    
    # Pass available actions that DO NOT include WAIT
    decision = agent.propose_action(mission, shared_state={}, history=[], available_actions=["OFFER"])
    
    # Agent intercepts and downgrades to ASK_CLARIFICATION
    assert decision.action == ActionType.ASK_CLARIFICATION
    assert "hallucinated action" in decision.explanation

def test_05_prompt_construction(mission, base_prompt_args):
    provider = MockProvider("{}") # Trigger fallback, but we just want to check last_prompt
    agent = PersonalAgent(provider)
    
    agent.propose_action(mission, **base_prompt_args)
    
    prompt = provider.last_prompt
    assert "objective: Buy laptop" in prompt
    assert "price <= 40000" in prompt
    assert "current_offer: 45000" in prompt
    assert "Counterparty: I want 45000" in prompt
    assert "AVAILABLE ACTIONS: OFFER, COUNTER" in prompt
