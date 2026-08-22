from pydantic import BaseModel, Field
from typing import List

class Mission(BaseModel):
    objective: str = Field(default="", description="The main goal of the negotiation")
    private_constraints: List[str] = Field(default_factory=list, description="Private rules never to be shared")
    required_conditions: List[str] = Field(default_factory=list, description="Things that must be met")
    preferences: List[str] = Field(default_factory=list, description="Nice to have features or conditions")
    authority_rules: List[str] = Field(default_factory=list, description="Escalation logic or approval rules")
