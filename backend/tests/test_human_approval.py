import pytest
from app.negotiation.human_approval import HumanApprovalEngine, HumanApprovalRequest
from app.missions.schemas import ExtractedMission

def test_generate_approval_request():
    engine = HumanApprovalEngine()
    req = engine.generate_approval_request({"price": 42000}, "delivery will take 15 days")
    
    assert req.what_happened == "The other party introduced a new term not covered by your instructions."
    assert req.new_condition == "delivery will take 15 days"
    assert req.current_offer["price"] == 42000

def test_process_modification_adds_constraint_without_overwriting():
    engine = HumanApprovalEngine()
    
    mission = ExtractedMission(
        objective="Buy laptop",
        hard_constraints=[{"key": "price", "operator": "<=", "value": 42000, "visibility": "PRIVATE", "type": "HARD"}],
        permissions=[]
    )
    
    # User modifies with voice
    instruction = "Delivery should be maximum 7 days."
    updated_mission = engine.process_modification(mission, instruction)
    
    # Check that price constraint is STILL THERE
    assert len(updated_mission.hard_constraints) == 2
    assert updated_mission.hard_constraints[0].key == "price"
    assert updated_mission.hard_constraints[0].value == 42000
    
    # Check that new constraint was added
    assert updated_mission.hard_constraints[1].key == "delivery_days"
    assert updated_mission.hard_constraints[1].value == 7
    assert updated_mission.hard_constraints[1].operator == "<="
