from app.voice.schemas import TranscriptResponse
from app.voice.providers import SpeechToTextProvider
from app.voice.normalizer import VoiceNormalizer
import re

class VoiceProcessor:
    """Orchestrates Voice to Text, Normalization, and Confirmation Flows."""
    
    def __init__(self, stt_provider: SpeechToTextProvider):
        self.stt_provider = stt_provider
        self.normalizer = VoiceNormalizer()
        
        # Simple heuristics for constraint detection requiring confirmation
        self.constraint_keywords = [
            "maximum", "max", "limit", "budget", 
            "se upar mat", "se zyada mat", "not more than"
        ]

    def process_audio(self, audio_data: bytes) -> TranscriptResponse:
        # 1. Transcribe audio to text
        raw_transcript = self.stt_provider.transcribe(audio_data)
        
        # 2. Normalize expressions (Hinglish/Monetary)
        normalized_text = self.normalizer.normalize_monetary_expressions(raw_transcript)
        
        # 3. Detect critical constraints that need confirmation
        requires_confirmation = False
        confirmation_prompt = None
        
        text_lower = normalized_text.lower()
        if any(kw in text_lower for kw in self.constraint_keywords):
            # Attempt to find the numeric limit they mentioned
            numbers = re.findall(r'₹(\d+)', normalized_text)
            if not numbers:
                numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', normalized_text)
                
            if numbers:
                limit = numbers[-1] # Usually the limit is stated near the end
                requires_confirmation = True
                confirmation_prompt = (
                    f"I understood your constraint as {limit}. Is that correct? "
                    "You can CONFIRM, EDIT, or CANCEL."
                )
            else:
                requires_confirmation = True
                confirmation_prompt = (
                    "I detected a constraint but couldn't understand the exact number. "
                    "Please EDIT your instruction or CANCEL."
                )

        return TranscriptResponse(
            original_transcript=raw_transcript,
            normalized_transcript=normalized_text,
            requires_confirmation=requires_confirmation,
            confirmation_prompt=confirmation_prompt
        )
