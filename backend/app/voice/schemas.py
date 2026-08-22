from pydantic import BaseModel, Field
from typing import Optional, List

class TranscriptResponse(BaseModel):
    original_transcript: str = Field(description="The raw output from the STT engine.")
    normalized_transcript: str = Field(description="Transcript after monetary and cultural normalization.")
    requires_confirmation: bool = Field(default=False, description="True if critical constraints were detected requiring user sign-off.")
    confirmation_prompt: Optional[str] = Field(None, description="The message asking the user to CONFIRM, EDIT, or CANCEL.")
