import pytest
from app.voice.tts_providers import MockTTSProvider
from app.voice.tts_processor import TTSProcessor

@pytest.mark.anyio
async def test_01_tts_success():
    provider = MockTTSProvider(fail=False)
    processor = TTSProcessor(provider)
    
    text, audio_stream = await processor.process_response("Hello, this is a test.")
    
    # 1. Text is returned immediately and identically
    assert text == "Hello, this is a test."
    
    # 2. Audio chunks are yielded
    chunks = []
    async for chunk in audio_stream:
        chunks.append(chunk)
        
    assert len(chunks) == 1
    assert chunks[0] == b"mock_audio_bytes"

@pytest.mark.anyio
async def test_02_tts_failure_graceful_fallback():
    provider = MockTTSProvider(fail=True)
    processor = TTSProcessor(provider)
    
    # 1. Even if TTS engine crashes, text must still be returned immediately
    text, audio_stream = await processor.process_response("Fallback text")
    assert text == "Fallback text"
    
    # 2. When the consumer tries to read the stream, it catches the error and yields nothing,
    # preventing the app from crashing.
    chunks = []
    async for chunk in audio_stream:
        chunks.append(chunk)
        
    assert len(chunks) == 0
