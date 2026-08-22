import enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class Personality(str, enum.Enum):
    FRIENDLY = "Friendly"
    AGGRESSIVE = "Aggressive"
    DIFFICULT = "Difficult"
    INDECISIVE = "Indecisive"
    RATIONAL = "Rational"

class SimState(BaseModel):
    starting_price: float
    minimum_price: float
    current_offer: float
    turn_count: int = 0
