from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any

class ConstraintSchema(BaseModel):
    key: str = Field(description="The attribute being constrained (e.g., 'price', 'quantity', 'projector')")
    operator: str = Field(description="Comparison operator: '<=', '>=', '==', 'contains'")
    value: Any = Field(description="The value of the constraint")
    visibility: str = Field(description="'PRIVATE' or 'SHARED'")
    type: str = Field(description="'HARD' or 'SOFT'")

class PermissionSchema(BaseModel):
    action: str = Field(description="The action being permitted (e.g., 'negotiate', 'close_deal', 'reveal_budget')")
    is_allowed: bool

class ExtractedMission(BaseModel):
    objective: str = Field(description="The main goal of the mission")
    target: Optional[str] = Field(None, description="Ideal outcome target (e.g., '40000')")
    ideal_outcome: Optional[str] = Field(None, description="Description of the ideal outcome")
    acceptable_outcome: Optional[str] = Field(None, description="Description of a minimally acceptable outcome")
    hard_constraints: List[ConstraintSchema] = Field(default_factory=list, description="Mandatory constraints that cannot be broken")
    soft_preferences: List[ConstraintSchema] = Field(default_factory=list, description="Preferences that are nice to have")
    permissions: List[PermissionSchema] = Field(default_factory=list, description="Explicit permissions given to the agent")
    escalation_rules: List[str] = Field(default_factory=list, description="Conditions under which human intervention is required")
    communication_preference: Optional[str] = Field(None, description="Preferred style or channel")
    missing_critical_info: List[str] = Field(default_factory=list, description="List of critical constraints that are vaguely defined or missing")

    @field_validator('hard_constraints')
    def validate_hard_constraints(cls, v):
        for c in v:
            if c.type != 'HARD':
                raise ValueError(f"Constraint {c.key} in hard_constraints must have type 'HARD'")
        return v
