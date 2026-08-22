from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class SpeechToTextProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_data: bytes) -> str:
        pass

class LocalSpeechToTextProvider(SpeechToTextProvider):
    """
    Faster-whisper implementation for STT.
    Architected to drop-in faster-whisper without heavy dependencies during hackathon scaffolding.
    """
    def __init__(self, model_size="tiny", device="cpu", compute_type="int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        # import faster_whisper
        # self.model = faster_whisper.WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_data: bytes) -> str:
        # In a real setup, we write bytes to temp file, then:
        # segments, info = self.model.transcribe(temp_file_path, beam_size=5)
        # return " ".join([segment.text for segment in segments])
        
        logger.info(f"Mocking transcription of {len(audio_data)} bytes using faster-whisper logic.")
        return "mock transcription"

class MockSTTProvider(SpeechToTextProvider):
    def __init__(self, expected_response: str):
        self.expected_response = expected_response
        
    def transcribe(self, audio_data: bytes) -> str:
        return self.expected_response
