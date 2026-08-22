import pytest
import json
import asyncio
from app.voice.providers import MockSTTProvider
from app.voice.processor import VoiceProcessor
from app.missions.engine import MissionParser, MissionValidator
from app.negotiation.engine import NegotiationEngine
from app.negotiation.schemas import NegotiationState, LLMRecommendation
from app.communication.fake_channel import FakeChannel
from app.evaluation.simulation_partner import SimulationPartner, Personality
from app.verification.engine import AgreementVerifier
from app.voice.tts_providers import MockTTSProvider
from app.voice.tts_processor import TTSProcessor

@pytest.mark.anyio
async def test_e2e_voice_to_agreement_pipeline():
    # 1. User speaks:
    audio_input = "Rahul se laptop ka price negotiate karo. 40,000 target hai. 42,000 se zyada mat jaana. Bag mil raha ho to 42,000 tak ja sakte ho."
    
    # 2. STT Transcribes and VoiceProcessor Normalizes
    stt_provider = MockSTTProvider(audio_input)
    voice_processor = VoiceProcessor(stt_provider)
    transcript_response = voice_processor.process_audio(b"fake_audio")
    
    assert "40000" in transcript_response.normalized_transcript
    assert "42000" in transcript_response.normalized_transcript
    assert transcript_response.requires_confirmation is True # "se zyada mat" triggered it
    
    # 3. Extract Mission (mock LLM extraction)
    mock_llm_json = json.dumps({
        "objective": "Negotiate laptop price with Rahul",
        "hard_constraints": [
            {"key": "price", "operator": "<=", "value": 42000, "visibility": "PRIVATE", "type": "HARD"},
            {"key": "vendor", "operator": "==", "value": "Rahul", "visibility": "SHARED", "type": "HARD"}
        ],
        "permissions": [
            {"action": "close_deal", "is_allowed": True},
            {"action": "make_offers", "is_allowed": True}
        ]
    })
    
    mission_parser = MissionParser()
    raw_mission = mission_parser.parse_mock(mock_llm_json)
    
    validator = MissionValidator()
    mission, clarifications = validator.validate(raw_mission)
    
    assert mission is not None
    assert len(clarifications) == 0
    
    # 6. Starts Negotiation
    channel = FakeChannel()
    engine = NegotiationEngine(mission, channel)
    
    # We will mock the PersonalAgent's LLM outputs to guide the negotiation deterministically
    engine.llm_mock = [
        LLMRecommendation(intent="COUNTER", dialogue="I can offer 38000.", proposed_offer={"price": 38000, "vendor": "Rahul"}),
        LLMRecommendation(intent="COUNTER", dialogue="How about 40000?", proposed_offer={"price": 40000, "vendor": "Rahul"}),
        LLMRecommendation(intent="ACCEPT", dialogue="I agree to 41500.", proposed_offer={"price": 41500, "vendor": "Rahul"})
    ]
    
    # 7. Setup Simulation Partner (Seller)
    seller = SimulationPartner(
        role="Seller", 
        starting_price=45000, 
        minimum_price=41000, 
        personality=Personality.RATIONAL,
        seed=101
    )
    
    # Seller opens
    seller_msg, seller_offer = seller.generate_opening()
    
    # 8. AI Negotiates
    turn = 0
    while engine.state not in [NegotiationState.AGREED, NegotiationState.FAILED, NegotiationState.WALKED_AWAY]:
        # Engine processes incoming
        formatted_incoming = f"{seller_msg} offer: {seller_offer['price']}"
        engine.process_turn(formatted_incoming)
        
        agent_msg = channel.sent_messages.pop(0) if channel.sent_messages else None
        if not agent_msg:
            break
            
        if engine.state == NegotiationState.AGREED:
            break
            
        agent_offer_val = engine.previous_offers[-1]["price"] if engine.previous_offers else 0
        seller_msg, seller_offer, intent = seller.process_offer(agent_offer_val)
        
        turn += 1
        if turn > 10:
            break
            
    assert engine.state == NegotiationState.AGREED
    assert engine.previous_offers[-1]["price"] == 41500
    
    # 9. Agreement is verified
    agreed_terms = {"price": 41500, "vendor": "Rahul"}
    verifier = AgreementVerifier()
    verification_result = verifier.verify(agreed_terms, mission)
    
    assert verification_result.valid is True
    assert verification_result.confidence == 1.0
    
    # 10. Agent speaks final result
    tts_provider = MockTTSProvider()
    tts_processor = TTSProcessor(tts_provider)
    
    final_text = "The negotiation is complete. We agreed on 41500."
    text_out, audio_stream = await tts_processor.process_response(final_text)
    
    assert text_out == final_text
    chunks = [chunk async for chunk in audio_stream]
    assert chunks[0] == b"mock_audio_bytes"
