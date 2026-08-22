from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from app.voice.processor import VoiceProcessor
from app.voice.providers import LocalSpeechToTextProvider, MockSTTProvider
from app.voice.tts_processor import TTSProcessor
from app.voice.tts_providers import MockTTSProvider
from app.communication.websocket_manager import manager
import logging
import io

logger = logging.getLogger(__name__)
router = APIRouter()

# For a real implementation, we'd inject this via dependencies
mock_stt = MockSTTProvider("Mock transcribed counterparty voice")
voice_processor = VoiceProcessor(mock_stt)

mock_tts = MockTTSProvider()
tts_processor = TTSProcessor(mock_tts)

@router.post("/turn")
async def process_voice_turn(audio: UploadFile = File(...), token: str = Form(...)):
    """
    Receives an audio blob (WebM) from the frontend VAD service.
    Processes it via STT -> Normalizer -> Negotiation Engine -> TTS.
    Streams TTS audio bytes back to the frontend to pipe into WebRTC.
    """
    if token not in manager.valid_tokens:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    auth = manager.valid_tokens[token]
    session_id = auth["session_id"]
    participant_id = auth["participant_id"]
    
    # 1. Read Audio
    audio_bytes = await audio.read()
    
    # 2. Process Voice (STT + Normalization)
    transcript_res = voice_processor.process_audio(audio_bytes)
    
    # We would normally route `transcript_res.normalized_transcript` to the NegotiationEngine here,
    # and get back the Agent's response string.
    # For now, we mock the Agent's decision text:
    agent_text = "I heard you say: " + transcript_res.normalized_transcript + ". Let me think about that."
    
    # 3. Process TTS
    text, audio_stream = await tts_processor.process_response(agent_text)
    
    # Return a StreamingResponse so frontend can play chunks immediately
    return StreamingResponse(audio_stream, media_type="audio/wav")
