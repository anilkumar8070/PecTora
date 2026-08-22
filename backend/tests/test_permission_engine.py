import pytest
from app.permissions.schemas import ActionRequest, PermissionRule, Condition
from app.permissions.engine import PermissionEvaluator

@pytest.fixture
def evaluator():
    return PermissionEvaluator()

def test_01_allow_without_conditions(evaluator):
    rules = [PermissionRule(action="CAN_NEGOTIATE", is_allowed=True)]
    req = ActionRequest(action="NEGOTIATE")
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_02_deny_without_conditions(evaluator):
    rules = [PermissionRule(action="CAN_CLOSE_DEAL", is_allowed=False)]
    req = ActionRequest(action="CLOSE_DEAL")
    res = evaluator.evaluate(req, rules)
    assert res.allowed is False
    assert "Explicitly blocked" in res.reason

def test_03_no_rule_found(evaluator):
    rules = [PermissionRule(action="CAN_NEGOTIATE", is_allowed=True)]
    req = ActionRequest(action="CLOSE_DEAL")
    res = evaluator.evaluate(req, rules)
    assert res.allowed is False
    assert "No explicit permission granted" in res.reason

def test_04_allow_with_condition_met(evaluator):
    rules = [
        PermissionRule(
            action="CAN_ACCEPT", 
            is_allowed=True, 
            conditions=[Condition(key="price", operator="<=", value=42000)]
        )
    ]
    req = ActionRequest(action="ACCEPT", payload={"price": 40000})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_05_allow_with_condition_unmet(evaluator):
    rules = [
        PermissionRule(
            action="CAN_ACCEPT", 
            is_allowed=True, 
            conditions=[Condition(key="price", operator="<=", value=42000)]
        )
    ]
    req = ActionRequest(action="ACCEPT", payload={"price": 43000})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is False
    assert "price (43000) must be <= 42000" in res.reason

def test_06_multiple_conditions_and_logic_met(evaluator):
    rules = [
        PermissionRule(
            action="CAN_ACCEPT", 
            is_allowed=True, 
            conditions=[
                Condition(key="price", operator="<=", value=42000),
                Condition(key="projector", operator="==", value=True)
            ]
        )
    ]
    req = ActionRequest(action="ACCEPT", payload={"price": 40000, "projector": True})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_07_multiple_conditions_and_logic_unmet(evaluator):
    rules = [
        PermissionRule(
            action="CAN_ACCEPT", 
            is_allowed=True, 
            conditions=[
                Condition(key="price", operator="<=", value=42000),
                Condition(key="projector", operator="==", value=True)
            ]
        )
    ]
    req = ActionRequest(action="ACCEPT", payload={"price": 40000, "projector": False})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is False
    assert "projector (False) must be == True" in res.reason

def test_08_missing_payload_key_for_condition(evaluator):
    rules = [
        PermissionRule(
            action="CAN_ACCEPT", 
            is_allowed=True, 
            conditions=[Condition(key="price", operator="<=", value=42000)]
        )
    ]
    req = ActionRequest(action="ACCEPT", payload={})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is False
    assert "missing from payload" in res.reason

def test_09_exists_operator_met(evaluator):
    rules = [
        PermissionRule(
            action="CAN_COUNTER", 
            is_allowed=True, 
            conditions=[Condition(key="reason", operator="exists", value=None)]
        )
    ]
    req = ActionRequest(action="COUNTER", payload={"reason": "too expensive"})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_10_exists_operator_unmet(evaluator):
    rules = [
        PermissionRule(
            action="CAN_COUNTER", 
            is_allowed=True, 
            conditions=[Condition(key="reason", operator="exists", value=None)]
        )
    ]
    req = ActionRequest(action="COUNTER", payload={"price": 40000})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is False
    assert "Missing required parameter" in res.reason

def test_11_string_contains_met(evaluator):
    rules = [
        PermissionRule(
            action="CAN_DISCLOSE", 
            is_allowed=True, 
            conditions=[Condition(key="info", operator="contains", value="timeline")]
        )
    ]
    req = ActionRequest(action="DISCLOSE", payload={"info": "We have a strict timeline."})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_12_type_coercion_string_to_int(evaluator):
    rules = [
        PermissionRule(
            action="CAN_ACCEPT", 
            is_allowed=True, 
            conditions=[Condition(key="price", operator="<=", value="42000")]
        )
    ]
    req = ActionRequest(action="ACCEPT", payload={"price": 40000}) # payload has int
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_13_type_coercion_int_to_string(evaluator):
    rules = [
        PermissionRule(
            action="CAN_ACCEPT", 
            is_allowed=True, 
            conditions=[Condition(key="price", operator="<=", value=42000)]
        )
    ]
    req = ActionRequest(action="ACCEPT", payload={"price": "40000"}) # payload has str
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_14_deny_rule_overrides_allow(evaluator):
    rules = [
        PermissionRule(action="CAN_ACCEPT", is_allowed=True, conditions=[Condition(key="price", operator="<=", value=42000)]),
        PermissionRule(action="CAN_ACCEPT", is_allowed=False, conditions=[Condition(key="vendor", operator="==", value="blacklisted")])
    ]
    req = ActionRequest(action="ACCEPT", payload={"price": 40000, "vendor": "blacklisted"})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is False
    assert "Explicitly blocked" in res.reason

def test_15_deny_rule_does_not_trigger_if_condition_unmet(evaluator):
    rules = [
        PermissionRule(action="CAN_ACCEPT", is_allowed=True, conditions=[Condition(key="price", operator="<=", value=42000)]),
        PermissionRule(action="CAN_ACCEPT", is_allowed=False, conditions=[Condition(key="vendor", operator="==", value="blacklisted")])
    ]
    req = ActionRequest(action="ACCEPT", payload={"price": 40000, "vendor": "approved"})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_16_action_name_case_insensitivity(evaluator):
    rules = [PermissionRule(action="can_accept", is_allowed=True)]
    req = ActionRequest(action="AccepT")
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_17_unknown_operator(evaluator):
    rules = [PermissionRule(action="CAN_ACCEPT", is_allowed=True, conditions=[Condition(key="price", operator="MAGIC", value=1)])]
    req = ActionRequest(action="ACCEPT", payload={"price": 1})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is False
    assert "Unknown operator MAGIC" in res.reason

def test_18_greater_than_operator(evaluator):
    rules = [PermissionRule(action="CAN_ACCEPT", is_allowed=True, conditions=[Condition(key="price", operator=">", value=40000)])]
    req = ActionRequest(action="ACCEPT", payload={"price": 40001})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_19_not_equal_operator(evaluator):
    rules = [PermissionRule(action="CAN_ACCEPT", is_allowed=True, conditions=[Condition(key="color", operator="!=", value="red")])]
    req = ActionRequest(action="ACCEPT", payload={"color": "blue"})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is True

def test_20_empty_payload_when_payload_needed(evaluator):
    rules = [PermissionRule(action="CAN_ACCEPT", is_allowed=True, conditions=[Condition(key="price", operator="<=", value=1)])]
    req = ActionRequest(action="ACCEPT", payload={})
    res = evaluator.evaluate(req, rules)
    assert res.allowed is False
    assert "missing from payload" in res.reason
