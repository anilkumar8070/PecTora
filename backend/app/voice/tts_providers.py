from abc import ABC, abstractmethod
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class TextToSpeechProvider(ABC):
    @abstractmethod
    async def synthesize_stream(self, text: str, voice: str) -> AsyncGenerator[bytes, None]:
        pass

class LocalTTSProvider(TextToSpeechProvider):
    """
    Piper-compatible local TTS implementation.
    Designed for streaming chunks of audio back to the frontend.
    """
    def __init__(self, model_dir: str = "models/piper"):
        self.model_dir = model_dir
        # import piper
        # self.model = piper.PiperVoice.load(model_dir)

    async def synthesize_stream(self, text: str, voice: str = "en-us-default") -> AsyncGenerator[bytes, None]:
        # In a real environment, this yields chunked WAV or PCM bytes from Piper
        try:
            logger.info(f"Synthesizing '{text}' with voice {voice} using Piper")
            # Mocking a chunked stream
            yield b"RIFF" # mock wav header
            yield b"audio_chunk_1"
            yield b"audio_chunk_2"
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise e

class MockTTSProvider(TextToSpeechProvider):
    def __init__(self, fail=False):
        self.fail = fail

    async def synthesize_stream(self, text: str, voice: str) -> AsyncGenerator[bytes, None]:
        if self.fail:
            raise RuntimeError("Mock TTS Engine crashed.")
        yield b"mock_audio_bytes"
