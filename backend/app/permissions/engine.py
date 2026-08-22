from typing import List, Dict, Any
from app.permissions.schemas import ActionRequest, PermissionRule, AuthorizationResult, Condition

class PermissionEvaluator:
    """
    Deterministically evaluates if an LLM requested action is allowed based on explicit rules.
    """
    
    def evaluate(self, request: ActionRequest, rules: List[PermissionRule]) -> AuthorizationResult:
        # Standardize action name matching (e.g. "ACCEPT" matches "CAN_ACCEPT")
        req_action = request.action.upper().replace("CAN_", "")
        expected_rule_action = f"CAN_{req_action}"
        
        matching_rules = [r for r in rules if r.action.upper() == expected_rule_action]
        
        if not matching_rules:
            return AuthorizationResult(
                allowed=False, 
                reason=f"DENIED. No explicit permission granted for {request.action}."
            )
        
        # Check DENY rules first (Deny overrides Allow)
        for rule in matching_rules:
            if not rule.is_allowed:
                if self._conditions_met(rule.conditions, request.payload):
                    return AuthorizationResult(
                        allowed=False, 
                        reason=f"DENIED. Explicitly blocked by rule: {rule.action} with conditions."
                    )
        
        # Check ALLOW rules
        for rule in matching_rules:
            if rule.is_allowed:
                unmet_condition_reason = self._get_unmet_condition(rule.conditions, request.payload)
                if unmet_condition_reason is None: # None means all conditions met
                    return AuthorizationResult(
                        allowed=True, 
                        reason=f"AUTHORIZED by rule: {rule.action}"
                    )
                else:
                    # Keep track of why the allow rule failed to provide a precise reason
                    failed_allow_reason = unmet_condition_reason
                    
        return AuthorizationResult(
            allowed=False, 
            reason=f"DENIED. {failed_allow_reason}"
        )

    def _conditions_met(self, conditions: List[Condition], payload: Dict[str, Any]) -> bool:
        return self._get_unmet_condition(conditions, payload) is None

    def _get_unmet_condition(self, conditions: List[Condition], payload: Dict[str, Any]) -> str | None:
        """
        Returns None if all conditions are met. 
        Returns a string reason if a condition fails.
        """
        for cond in conditions:
            if cond.operator == 'exists':
                if cond.key not in payload:
                    return f"Missing required parameter '{cond.key}'"
                continue
                
            if cond.key not in payload:
                return f"Cannot evaluate {cond.key} {cond.operator} {cond.value}: '{cond.key}' missing from payload."
            
            payload_val = payload[cond.key]
            
            try:
                # Type coercion for safe comparison
                c_val = type(payload_val)(cond.value) if cond.value is not None else None
            except (ValueError, TypeError):
                c_val = str(cond.value)
                payload_val = str(payload_val)

            if cond.operator == '==':
                if not (payload_val == c_val): return f"{cond.key} ({payload_val}) must be == {c_val}"
            elif cond.operator == '!=':
                if not (payload_val != c_val): return f"{cond.key} ({payload_val}) must be != {c_val}"
            elif cond.operator == '<':
                if not (payload_val < c_val): return f"{cond.key} ({payload_val}) must be < {c_val}"
            elif cond.operator == '<=':
                if not (payload_val <= c_val): return f"{cond.key} ({payload_val}) must be <= {c_val}"
            elif cond.operator == '>':
                if not (payload_val > c_val): return f"{cond.key} ({payload_val}) must be > {c_val}"
            elif cond.operator == '>=':
                if not (payload_val >= c_val): return f"{cond.key} ({payload_val}) must be >= {c_val}"
            elif cond.operator == 'contains':
                if not isinstance(payload_val, (str, list, dict)) or c_val not in payload_val:
                    return f"{cond.key} must contain {c_val}"
            else:
                return f"Unknown operator {cond.operator}"
                
        return None
