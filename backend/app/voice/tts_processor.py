from typing import AsyncGenerator, Tuple
from app.voice.tts_providers import TextToSpeechProvider
import logging

logger = logging.getLogger(__name__)

class TTSProcessor:
    """Orchestrates TTS streaming and handles graceful fallbacks if TTS fails."""
    def __init__(self, provider: TextToSpeechProvider):
        self.provider = provider
        
    async def process_response(self, text: str, voice: str = "default") -> Tuple[str, AsyncGenerator[bytes, None]]:
        """
        Returns the original text and an async generator for the audio stream.
        If TTS fails to initialize or crashes mid-stream, it catches the error and stops yielding bytes,
        ensuring the text response (which was returned immediately) is never blocked.
        """
        
        async def safe_stream() -> AsyncGenerator[bytes, None]:
            try:
                # The generator yields bytes as Piper produces them
                async for chunk in self.provider.synthesize_stream(text, voice):
                    yield chunk
            except Exception as e:
                # Graceful fallback: log error, stop audio stream, frontend still has text
                logger.warning(f"TTS streaming failed, falling back to text-only: {e}")
                # We simply stop yielding. The websocket can send an END frame or similar.
        
        return text, safe_stream()
