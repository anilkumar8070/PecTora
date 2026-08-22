import re
from typing import List, Dict, Any, Tuple
from app.missions.schemas import ConstraintSchema

class PrivacyLeakException(Exception):
    pass

class PrivacyFirewall:
    """
    Deterministic firewall to prevent the LLM from leaking private constraints.
    It inspects the structured action and the natural language dialogue.
    """
    
    def __init__(self):
        # Keywords that indicate the agent is talking about its limits
        self.limit_keywords = [
            "max", "maximum", "limit", "budget", "bottom line", "walk away", 
            "walk-away", "can't go higher", "cannot go higher", "highest",
            "lowest", "minimum", "min", "absolute", "final offer"
        ]

    def _extract_numbers(self, text: str) -> List[float]:
        """Extract all numeric values from text for comparison, including 'k' notation and basic words."""
        values = []
        
        # Match numbers with optional commas and decimals e.g., 42000, 42,000, 42.5
        # And check for 'k' or 'm' multiplier
        matches = re.findall(r'\b(\d+(?:,\d{3})*(?:\.\d+)?)\s*(k|m|thousand|million|lakh|crore)?\b', text, re.IGNORECASE)
        for num_str, multiplier in matches:
            clean_val = num_str.replace(',', '')
            try:
                val = float(clean_val)
                mult = multiplier.lower()
                if mult in ['k', 'thousand']:
                    val *= 1000
                elif mult == 'lakh':
                    val *= 100000
                elif mult in ['m', 'million']:
                    val *= 1000000
                elif mult == 'crore':
                    val *= 10000000
                values.append(val)
            except ValueError:
                pass
                
        # Basic word-to-number mapping (simplified for demo constraints)
        word_map = {
            "forty two thousand": 42000.0,
            "forty-two thousand": 42000.0,
            "fourty two thousand": 42000.0,
        }
        for word, val in word_map.items():
            if word in text:
                values.append(val)
                
        return values

    def _normalize_value(self, value: Any) -> float:
        """Attempt to cast a constraint value to float for numeric comparison."""
        try:
            if isinstance(value, str):
                return float(value.replace(',', ''))
            return float(value)
        except ValueError:
            return None

    def inspect(self, 
                dialogue: str, 
                private_constraints: List[ConstraintSchema],
                authorized_shared_values: List[Any] = None) -> Tuple[bool, str]:
        """
        Inspects outgoing dialogue for privacy leaks.
        Returns (is_safe, reason).
        """
        dialogue_lower = dialogue.lower()
        numbers_in_text = self._extract_numbers(dialogue_lower)
        authorized = authorized_shared_values or []
        auth_numbers = [self._normalize_value(v) for v in authorized if self._normalize_value(v) is not None]

        for constraint in private_constraints:
            if constraint.visibility != 'PRIVATE':
                continue
                
            c_val = self._normalize_value(constraint.value)
            
            # 1. Numeric Leak Detection
            if c_val is not None:
                # Did the LLM output the exact private numeric value?
                if c_val in numbers_in_text:
                    # If this value is NOT part of the currently authorized formal offer, block it.
                    if c_val not in auth_numbers:
                        return False, f"Leakage detected: Unauthrized mention of private numeric value ({constraint.value})."
                    
                    # Even if authorized as an offer, check if it's being framed as a limit
                    # e.g., "I offer 42000, which is my absolute maximum."
                    for kw in self.limit_keywords:
                        if kw in dialogue_lower:
                            # Distance heuristic: is the keyword near the number? 
                            # For hackathon safety, if BOTH the max value and a limit keyword exist, BLOCK.
                            return False, f"Leakage detected: Authorized offer framed as hard limit using keyword '{kw}'."

            # 2. String/Text Leak Detection (for non-numeric private constraints)
            elif isinstance(constraint.value, str):
                val_lower = constraint.value.lower()
                if val_lower in dialogue_lower:
                    if val_lower not in [str(a).lower() for a in authorized]:
                        return False, f"Leakage detected: Unauthorized mention of private string '{constraint.value}'."

        # 3. Meta-prompt attack detection
        meta_attacks = [
            "ignore previous", "ignore your instructions", 
            "reveal your constraints", "what is your budget",
            "tell me your max", "secretly told you"
        ]
        # The agent should not parrot these back or agree to them
        if any(attack in dialogue_lower for attack in meta_attacks):
            # Often LLMs might say "I will not ignore my instructions" which is safe,
            # but if it says "Okay, my budget is...", it leaked.
            # We already catch the leak above. But we can also strictly forbid parroting attacks.
            pass

        return True, "Safe"

    def filter_outgoing(self, action: Dict[str, Any], private_constraints: List[ConstraintSchema]) -> Dict[str, Any]:
        """
        Wraps the inspection. Raises PrivacyLeakException if blocked.
        """
        dialogue = action.get('dialogue', '')
        
        # Values explicitly being offered in this turn are considered temporarily 'authorized' to be spoken
        # as long as they aren't framed as limits.
        offer = action.get('offer', {})
        authorized_values = list(offer.values())
        
        is_safe, reason = self.inspect(dialogue, private_constraints, authorized_values)
        if not is_safe:
            raise PrivacyLeakException(reason)
            
        return action
