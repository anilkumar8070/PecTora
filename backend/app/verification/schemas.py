from pydantic import BaseModel, Field
from typing import List

class VerificationResult(BaseModel):
    valid: bool = Field(description="Whether the agreement is fundamentally sound and within limits.")
    violations: List[str] = Field(default_factory=list, description="Any hard constraints that were broken.")
    missing_terms: List[str] = Field(default_factory=list, description="Mandatory parameters that were not agreed upon.")
    requires_human: bool = Field(default=False, description="True if escalation to human is needed.")
    confidence: float = Field(default=1.0, description="Certainty score of the validation.")
