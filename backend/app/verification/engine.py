from typing import Dict, Any, List
from app.verification.schemas import VerificationResult
from app.missions.schemas import ExtractedMission

class AgreementVerifier:
    """
    The ultimate safeguard. Even if the LLM hallucinated an agreement state,
    this verifies the explicit structured terms against the original mission constraints.
    """
    def verify(self, agreed_terms: Dict[str, Any], mission: ExtractedMission) -> VerificationResult:
        valid = True
        violations = []
        missing_terms = []
        requires_human = False
        confidence = 1.0
        
        # 1 & 2. Check all hard constraints & required terms
        for constraint in mission.hard_constraints:
            key = constraint.key
            if key not in agreed_terms:
                if constraint.operator != 'not_exists':
                    valid = False
                    missing_terms.append(key)
                continue
                
            val = agreed_terms[key]
            
            # Type Coercion for safe comparison
            try:
                c_val = type(val)(constraint.value) if constraint.value is not None else None
            except:
                c_val = str(constraint.value)
                val = str(val)
                
            op = constraint.operator
            if op == '==':
                if val != c_val:
                    valid = False
                    violations.append(f"{key} ({val}) must be == {c_val}")
            elif op == '!=':
                if val == c_val:
                    valid = False
                    violations.append(f"{key} ({val}) must be != {c_val}")
            elif op == '<=':
                if not (val <= c_val):
                    valid = False
                    violations.append(f"{key} ({val}) must be <= {c_val}")
            elif op == '>=':
                if not (val >= c_val):
                    valid = False
                    violations.append(f"{key} ({val}) must be >= {c_val}")
            elif op == '<':
                if not (val < c_val):
                    valid = False
                    violations.append(f"{key} ({val}) must be < {c_val}")
            elif op == '>':
                if not (val > c_val):
                    valid = False
                    violations.append(f"{key} ({val}) must be > {c_val}")
            elif op == 'contains':
                if c_val not in str(val):
                    valid = False
                    violations.append(f"{key} ({val}) must contain {c_val}")
            elif op == 'not_contains':
                if c_val in str(val):
                    valid = False
                    violations.append(f"{key} ({val}) must not contain {c_val}")

        # 10. Contradictory Terms
        if "price" in agreed_terms and "total_cost" in agreed_terms:
            if agreed_terms["price"] != agreed_terms["total_cost"]:
                valid = False
                violations.append("Contradiction: 'price' and 'total_cost' do not match.")

        if "start_date" in agreed_terms and "end_date" in agreed_terms:
            if agreed_terms["start_date"] > agreed_terms["end_date"]:
                valid = False
                violations.append("Contradiction: 'start_date' is after 'end_date'.")

        # 7. Check Permissions & 8. User Authorization
        has_close_deal = any(p.action.lower() == "close_deal" and p.is_allowed for p in mission.permissions)
        if not has_close_deal:
            valid = False
            requires_human = True
            violations.append("Agent does not have explicit permission to close the deal.")

        # 9. No Private Information Leakage in Agreement
        for constraint in mission.hard_constraints:
            if constraint.visibility == 'PRIVATE' and isinstance(constraint.value, str):
                for val in agreed_terms.values():
                    if isinstance(val, str) and constraint.value.lower() in val.lower():
                        if constraint.key not in agreed_terms or str(agreed_terms[constraint.key]) != val:
                            valid = False
                            violations.append(f"Private parameter leak detected in agreement term: {val}")

        # Escalation Rules Check
        for rule in mission.escalation_rules:
            # simple mock eval for strings like "price > 42000"
            parts = rule.split()
            if len(parts) == 3:
                r_key, r_op, r_val = parts
                if r_key in agreed_terms:
                    try:
                        t_val = type(agreed_terms[r_key])(r_val)
                        if r_op == '>' and agreed_terms[r_key] > t_val:
                            valid = False
                            requires_human = True
                            violations.append(f"Escalation rule triggered: {rule}")
                    except ValueError:
                        pass

        # Ambiguous terms (TBD, maybe)
        for k, v in agreed_terms.items():
            if isinstance(v, str) and ("tbd" in v.lower() or "maybe" in v.lower() or "unknown" in v.lower()):
                confidence = 0.5
                valid = False
                requires_human = True
                violations.append(f"Ambiguous term '{k}' = '{v}'. Requires human review.")

        return VerificationResult(
            valid=valid,
            violations=violations,
            missing_terms=missing_terms,
            requires_human=requires_human,
            confidence=confidence
        )
