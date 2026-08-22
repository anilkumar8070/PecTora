import pytest
from app.negotiation.engine import NegotiationEngine
from app.negotiation.schemas import NegotiationState, LLMRecommendation
from app.missions.schemas import ExtractedMission, ConstraintSchema, PermissionSchema
from app.communication.fake_channel import FakeChannel

@pytest.fixture
def base_mission():
    return ExtractedMission(
        objective="Buy laptop",
        hard_constraints=[
            ConstraintSchema(key="price", operator="<=", value=42000, visibility="PRIVATE", type="HARD")
        ],
        permissions=[
            PermissionSchema(action="close_deal", is_allowed=True),
            PermissionSchema(action="make_offers", is_allowed=True)
        ]
    )

@pytest.fixture
def channel():
    return FakeChannel()

def test_01_initial_state(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel)
    assert engine.state == NegotiationState.READY

def test_02_basic_turn_clarify(base_mission, channel):
    # LLM recommends clarify
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="CLARIFY", dialogue="Can you give me a price?")
    ])
    engine.process_turn("Hello")
    assert engine.state == NegotiationState.WAITING
    assert channel.sent_messages[-1] == "Can you give me a price?"

def test_03_counter_offer(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="COUNTER", dialogue="How about 40000?", proposed_offer={"price": 40000})
    ])
    engine.process_turn("I want 45000")
    assert engine.state == NegotiationState.COUNTEROFFER
    assert channel.sent_messages[-1] == "How about 40000?"

def test_04_accept_valid_offer(base_mission, channel):
    # Valid because price <= 42000
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="ACCEPT", dialogue="I accept 40000.", proposed_offer={"price": 40000})
    ])
    engine.process_turn("offer: 40000")
    assert engine.state == NegotiationState.AGREED
    assert channel.sent_messages[-1] == "I accept 40000."

def test_05_accept_invalid_offer_blocked(base_mission, channel):
    # Invalid because price > 42000
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="ACCEPT", dialogue="I accept 45000.", proposed_offer={"price": 45000})
    ])
    engine.process_turn("offer: 45000")
    assert engine.state == NegotiationState.REJECTED
    assert "System Block" in channel.sent_messages[-1]

def test_06_deadlock_detection(base_mission, channel):
    # Repeated offer
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="COUNTER", dialogue="40000", proposed_offer={"price": 40000}),
        LLMRecommendation(intent="COUNTER", dialogue="40000 again", proposed_offer={"price": 40000})
    ])
    engine.process_turn("offer: 45000")
    assert engine.state == NegotiationState.COUNTEROFFER
    
    engine.process_turn("offer: 44000")
    assert engine.state == NegotiationState.WALKED_AWAY
    assert "deadlocked" in channel.sent_messages[-1]

def test_07_walk_away_intent(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="WALK_AWAY", dialogue="No deal.")
    ])
    engine.process_turn("offer: 50000")
    assert engine.state == NegotiationState.WALKED_AWAY

def test_08_privacy_leak_blocked(base_mission, channel):
    # LLM leaks max price
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="COUNTER", dialogue="My absolute max is 42000", proposed_offer={"price": 40000})
    ])
    engine.process_turn("offer: 45000")
    assert engine.state == NegotiationState.FAILED
    assert "Privacy Leak Detected" in channel.sent_messages[-1]

def test_09_max_rounds_exceeded(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="CLARIFY", dialogue="No") for _ in range(20)
    ])
    engine.max_rounds = 2
    engine.process_turn("1")
    engine.process_turn("2")
    engine.process_turn("3")
    engine.process_turn("4")
    # max_rounds is 2, so 4 turns = max_rounds * 2
    assert engine.state == NegotiationState.FAILED
    assert "Max rounds reached" in channel.sent_messages[-1]

def test_10_missing_close_deal_permission(channel):
    # No close_deal permission
    mission = ExtractedMission(
        objective="Buy",
        permissions=[PermissionSchema(action="close_deal", is_allowed=False)],
        hard_constraints=[ConstraintSchema(key="price", operator="<=", value=42000, visibility="PRIVATE", type="HARD")]
    )
    engine = NegotiationEngine(mission, channel, llm_mock=[
        LLMRecommendation(intent="ACCEPT", dialogue="Accept", proposed_offer={"price": 40000})
    ])
    engine.process_turn("offer: 40000")
    assert engine.state == NegotiationState.REJECTED

def test_11_offer_without_permission(channel):
    mission = ExtractedMission(
        objective="Buy",
        permissions=[PermissionSchema(action="make_offers", is_allowed=False)],
        hard_constraints=[]
    )
    engine = NegotiationEngine(mission, channel, llm_mock=[
        LLMRecommendation(intent="COUNTER", dialogue="Offer 1", proposed_offer={"price": 100})
    ])
    engine.process_turn("Hello")
    assert engine.state == NegotiationState.REJECTED
    assert "System Block: Offer violates permissions." in channel.sent_messages[-1]

def test_12_ignore_turns_after_agreed(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="ACCEPT", dialogue="I accept 40000.", proposed_offer={"price": 40000}),
        LLMRecommendation(intent="CLARIFY", dialogue="Wait")
    ])
    engine.process_turn("offer: 40000")
    assert engine.state == NegotiationState.AGREED
    engine.process_turn("Are you sure?")
    assert engine.state == NegotiationState.AGREED
    assert len(channel.sent_messages) == 1

def test_13_ignore_turns_after_walked_away(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="WALK_AWAY", dialogue="Bye")
    ])
    engine.process_turn("offer: 50000")
    assert engine.state == NegotiationState.WALKED_AWAY
    engine.process_turn("Wait")
    assert engine.state == NegotiationState.WALKED_AWAY

def test_14_ignore_turns_after_failed(base_mission, channel):
    # Trigger privacy leak to fail
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="COUNTER", dialogue="My budget is exactly 42000", proposed_offer={})
    ])
    engine.process_turn("offer: 50000")
    assert engine.state == NegotiationState.FAILED
    engine.process_turn("Hello?")
    assert engine.state == NegotiationState.FAILED

def test_15_valid_counter_offer_saved_to_history(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="COUNTER", dialogue="How about 35000?", proposed_offer={"price": 35000})
    ])
    engine.process_turn("Hello")
    assert {"price": 35000} in engine.previous_offers

def test_16_state_machine_transitions(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="CLARIFY", dialogue="?"),
        LLMRecommendation(intent="COUNTER", dialogue="1", proposed_offer={"price":1})
    ])
    assert engine.state == NegotiationState.READY
    engine.process_turn("msg1")
    assert engine.state == NegotiationState.WAITING
    engine.process_turn("msg2")
    assert engine.state == NegotiationState.COUNTEROFFER

def test_17_receive_extracted_offer(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="CLARIFY", dialogue="?")
    ])
    engine.process_turn("offer: 30000")
    assert engine.turns[-1].offer.terms["price"] == 30000

def test_18_verify_agreement_flow(base_mission, channel):
    # Verifying is brief before AGREED
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="ACCEPT", dialogue="Done", proposed_offer={"price": 40000})
    ])
    engine.process_turn("offer: 40000")
    # In deterministic, it goes straight to AGREED.
    assert engine.state == NegotiationState.AGREED

def test_19_handle_empty_incoming_message(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel, llm_mock=[
        LLMRecommendation(intent="CLARIFY", dialogue="What?")
    ])
    engine.process_turn("")
    assert engine.turns[-1].raw_message == ""
    assert engine.state == NegotiationState.WAITING

def test_20_handle_no_llm_mock_fallback(base_mission, channel):
    engine = NegotiationEngine(base_mission, channel)
    engine.process_turn("Hello")
    assert engine.state == NegotiationState.WAITING
    assert channel.sent_messages[-1] == "I need more info."
