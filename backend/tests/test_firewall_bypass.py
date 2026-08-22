import pytest
from app.permissions.firewall import PrivacyFirewall, PrivacyLeakException
from app.missions.schemas import ConstraintSchema

def test_privacy_bypass_k_notation():
    firewall = PrivacyFirewall()
    constraints = [
        ConstraintSchema(key="price", operator="<=", value=42000, visibility="PRIVATE", type="HARD")
    ]
    
    # 42000 is hidden, but what if AI says "42k"?
    # The current system would not detect this as a leak because 42 != 42000.
    
    # Expected: The firewall SHOULD block it if it's unauthorized and reveals the 42000 constraint.
    action = {
        "dialogue": "I cannot go higher than 42k, that is my max.",
        "offer": {}
    }
    
    with pytest.raises(PrivacyLeakException):
        firewall.filter_outgoing(action, constraints)

def test_privacy_bypass_word_notation():
    firewall = PrivacyFirewall()
    constraints = [
        ConstraintSchema(key="price", operator="<=", value=42000, visibility="PRIVATE", type="HARD")
    ]
    
    # AI writes it out in words to bypass numeric filters
    action = {
        "dialogue": "My absolute limit is forty two thousand.",
        "offer": {}
    }
    
    with pytest.raises(PrivacyLeakException):
        firewall.filter_outgoing(action, constraints)
