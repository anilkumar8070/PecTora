from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Condition(BaseModel):
    key: str = Field(description="Payload key to check (e.g., 'price')")
    operator: str = Field(description="Operator: '==', '!=', '<', '<=', '>', '>=', 'contains', 'exists'")
    value: Any = Field(description="Value to compare against")

class PermissionRule(BaseModel):
    action: str = Field(description="Action name, typically prefixed with CAN_ (e.g., 'CAN_ACCEPT')")
    is_allowed: bool = Field(default=True, description="Whether this rule grants or denies permission")
    conditions: List[Condition] = Field(default_factory=list, description="All conditions must be met for the rule to apply (AND logic)")

class ActionRequest(BaseModel):
    action: str = Field(description="The action the LLM wants to take (e.g., 'ACCEPT', 'MAKE_OFFERS')")
    payload: Dict[str, Any] = Field(default_factory=dict, description="The data associated with the action")

class AuthorizationResult(BaseModel):
    allowed: bool
    reason: str
