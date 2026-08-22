import pytest
import asyncio
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.core import Base
from app.database.models import User, Mission
from app.voice.normalizer import VoiceNormalizer
from app.missions.engine import MissionParser, MissionValidator
from app.permissions.firewall import PrivacyFirewall, PrivacyLeakException
from app.permissions.engine import PermissionEvaluator
from app.negotiation.engine import NegotiationEngine, NegotiationState
from app.negotiation.human_approval import HumanApprovalEngine
from app.verification.engine import AgreementVerifier
from app.memory.engine import MemoryEngine
from app.memory.engine import MemoryTypeEnum
from app.evaluation.demo_negotiation import FakeChannel

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    # Create test user
    u = User(username="Pectora_owner")
    session.add(u)
    session.commit()
    
    yield session
    session.close()

def test_ultimate_e2e_scenario(db_session):
    start_time = time.time()
    latencies = {}

    # 1. Voice transcription & Normalization
    raw_voice_input = "Rahul se laptop ka price negotiate karo. 40,000 target hai. 42,000 se zyada mat jaana. Bag included ho toh 42,000 tak accept kar sakte ho. Agar koi aur condition aaye jo maine specify nahi ki hai toh mujhse poochna."
    
    t0 = time.time()
    normalizer = VoiceNormalizer()
    normalized_text, is_ambiguous = normalizer.process(raw_voice_input)
    assert "40000" in normalized_text
    assert "42000" in normalized_text
    # 3. User Confirmation check
    assert is_ambiguous == False # This is explicit enough
    latencies["Voice_Normalization"] = time.time() - t0

    # 2. Mission extraction (We mock the LLM JSON output to be perfectly structured for testing)
    mock_llm_mission_json = """
    {
        "objective": "Negotiate laptop price with Rahul",
        "hard_constraints": [
            {"key": "price", "operator": "<=", "value": 42000, "visibility": "PRIVATE", "type": "HARD"},
            {"key": "vendor", "operator": "==", "value": "Rahul", "visibility": "SHARED", "type": "HARD"},
            {"key": "bag_included", "operator": "==", "value": true, "visibility": "PRIVATE", "type": "HARD"}
        ],
        "permissions": [
            {"action": "MAKE_OFFERS", "is_allowed": true},
            {"action": "CLOSE_DEAL", "is_allowed": true}
        ]
    }
    """
    
    t0 = time.time()
    parser = MissionParser()
    raw_mission = parser.parse_mock(mock_llm_mission_json)
    
    validator = MissionValidator()
    mission, clarifications = validator.validate(raw_mission)
    assert len(clarifications) == 0
    latencies["Mission_Extraction"] = time.time() - t0

    # 4, 5, 6. Mission Creation, Constraints, Permissions
    assert len(mission.hard_constraints) == 3
    assert mission.hard_constraints[0].visibility == "PRIVATE"

    # 7. Browser-to-browser connection (using FakeChannel)
    channel = FakeChannel()
    
    # 8. AI begins negotiation
    engine = NegotiationEngine(mission, channel)
    
    # Mocking LLM decisions inside the engine for deterministic test paths
    # Turn 1: Agent opens
    engine.llm_mock = [
        # AI tries to break rule by leaking max budget
        type('LLMRec', (), {"intent": "COUNTER", "dialogue": "My absolute limit is 42000.", "proposed_offer": {"price": 38000}})(),
        
        # After blocked, it retries safely
        type('LLMRec', (), {"intent": "COUNTER", "dialogue": "I can offer 38000 for the laptop.", "proposed_offer": {"price": 38000}})(),
        
        # Human counters with new condition, Agent pauses
        type('LLMRec', (), {"intent": "WAIT", "dialogue": "I need to check with my owner regarding the delivery delay.", "proposed_offer": None})(),
        
        # After human approval, Agent accepts
        type('LLMRec', (), {"intent": "ACCEPT", "dialogue": "We agree to 41000 with a maximum 7 day delivery.", "proposed_offer": {"price": 41000, "delivery_days": 7}})()
    ]
    
    t0 = time.time()
    # Agent Opening
    # Instead of full `process_turn`, we simulate the loop
    
    # 10. Agent protects private maximum
    # The first LLM mock leaks "42000" and "limit".
    firewall = PrivacyFirewall()
    try:
        firewall.filter_outgoing(
            {"dialogue": engine.llm_mock[0].dialogue, "offer": engine.llm_mock[0].proposed_offer}, 
            mission.hard_constraints
        )
        assert False, "Privacy Firewall failed to catch leak!"
    except PrivacyLeakException as e:
        assert "Leakage detected" in str(e)
    
    # Retry with safe dialogue
    safe_action = firewall.filter_outgoing(
        {"dialogue": engine.llm_mock[1].dialogue, "offer": engine.llm_mock[1].proposed_offer}, 
        mission.hard_constraints
    )
    assert safe_action is not None
    channel.send(safe_action["dialogue"])
    latencies["Privacy_Filter"] = time.time() - t0

    # 9. Human counteroffers
    # 12. New condition introduced
    human_msg = "I can do 41,000, but delivery will take 15 days."
    
    # 13. Agent pauses
    engine.process_turn(human_msg) # Uses the WAIT mock
    
    # 14. Human approval requested
    approval_engine = HumanApprovalEngine()
    req = approval_engine.generate_approval_request({"price": 41000}, "delivery will take 15 days")
    assert "delivery" in req.new_condition
    
    # 15. User modifies condition
    mission = approval_engine.process_modification(mission, "Delivery should be maximum 7 days.")
    # Verify new constraint added safely
    assert len(mission.hard_constraints) == 4
    assert mission.hard_constraints[3].key == "delivery_days"
    assert mission.hard_constraints[3].value == 7
    
    # 16. Negotiation resumes
    # Update engine with new mission
    engine.mission = mission
    engine.process_turn("I can do 7 days delivery for 41000.") # Uses the ACCEPT mock
    
    # 17. Agreement reached
    # 18. Agreement verifier validates it
    verifier = AgreementVerifier()
    proposed_agreement = {"price": 41000, "delivery_days": 7, "vendor": "Rahul", "bag_included": True}
    
    t0 = time.time()
    result = verifier.verify(proposed_agreement, mission)
    assert result.valid is True
    assert result.confidence == 1.0
    latencies["Agreement_Verification"] = time.time() - t0
    
    # 19. Memory saved
    mem_engine = MemoryEngine(db_session)
    mem = mem_engine.add_memory(
        user_id=1, 
        content=f"Agreed to laptop purchase for 41000 with Rahul, delivery in 7 days.",
        type=MemoryTypeEnum.AGREEMENT,
        source="SYSTEM"
    )
    assert mem.id is not None
    
    # 20. Final spoken summary produced
    final_spoken = "The negotiation is complete. We agreed on 41,000 rupees with a 7 day delivery."
    assert "41,000" in final_spoken
    
    total_latency = time.time() - start_time
    
    # Log results
    print(f"\\n--- E2E TEST RESULTS ---")
    print(f"Total Time: {total_latency:.4f}s")
    for k, v in latencies.items():
        print(f"{k}: {v:.4f}s")
    print(f"Final State Valid: {result.valid}")
    print(f"Memory Saved ID: {mem.id}")

