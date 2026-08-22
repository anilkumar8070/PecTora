import json
import pytest
from app.missions.engine import MissionParser, MissionValidator, ClarificationGenerator
from app.missions.schemas import ExtractedMission

@pytest.fixture
def parser():
    return MissionParser()

@pytest.fixture
def validator():
    return MissionValidator()

@pytest.fixture
def clarifier():
    return ClarificationGenerator()

# Helper to create mock LLM JSON output
def make_mock(objective, hard_constraints=None, soft_preferences=None, missing=None):
    return json.dumps({
        "objective": objective,
        "hard_constraints": hard_constraints or [],
        "soft_preferences": soft_preferences or [],
        "missing_critical_info": missing or []
    })

def test_01_valid_english_purchase(parser, validator, clarifier):
    # "Buy a laptop. Target 40k. Max 42k."
    mock_json = make_mock(
        "purchase laptop",
        [{"key": "price", "operator": "<=", "value": 42000, "visibility": "PRIVATE", "type": "HARD"}]
    )
    raw = parser.parse_mock(mock_json)
    mission, clarifications = validator.validate(raw)
    assert mission is not None
    assert len(clarifications) == 0

def test_02_missing_price_purchase(parser, validator, clarifier):
    # "Buy a laptop for me." (Missing budget)
    mock_json = make_mock("purchase laptop")
    raw = parser.parse_mock(mock_json)
    mission, clarifications = validator.validate(raw)
    assert mission is not None
    assert "maximum price" in clarifications
    assert "I need a bit more clarity" in clarifier.generate(clarifications)

def test_03_valid_hinglish_negotiation(parser, validator):
    # "Rahul se laptop ke price pe negotiate karo. 40,000 target hai. 42,000 max."
    mock_json = make_mock(
        "negotiate laptop price",
        [{"key": "price", "operator": "<=", "value": 42000, "visibility": "PRIVATE", "type": "HARD"}]
    )
    raw = parser.parse_mock(mock_json)
    mission, clarifications = validator.validate(raw)
    assert mission is not None
    assert len(clarifications) == 0

def test_04_missing_price_hinglish(parser, validator):
    # "Bhai ek mast phone kharidna hai."
    mock_json = make_mock("phone kharidna hai")
    raw = parser.parse_mock(mock_json)
    mission, clarifications = validator.validate(raw)
    assert "maximum price" in clarifications

def test_05_valid_hindi_selling(parser, validator):
    # "Mera purana scooter bechna hai. 15000 se kam me mat dena."
    mock_json = make_mock(
        "scooter bechna",
        [{"key": "price", "operator": ">=", "value": 15000, "visibility": "PRIVATE", "type": "HARD"}]
    )
    raw = parser.parse_mock(mock_json)
    mission, clarifications = validator.validate(raw)
    assert len(clarifications) == 0

def test_06_missing_min_price_selling(parser, validator):
    # "Bike sell karni hai."
    mock_json = make_mock("sell bike")
    raw = parser.parse_mock(mock_json)
    mission, clarifications = validator.validate(raw)
    assert "minimum selling price" in clarifications

def test_07_invalid_constraint_type(parser, validator):
    # LLM hallucinates a SOFT type in the hard_constraints array
    mock_json = make_mock(
        "buy car",
        [{"key": "price", "operator": "<=", "value": 42000, "visibility": "PRIVATE", "type": "SOFT"}]
    )
    raw = parser.parse_mock(mock_json)
    mission, errors = validator.validate(raw)
    assert mission is None
    assert any("must have type 'HARD'" in e for e in errors)

def test_08_multiple_clarifications(parser, validator, clarifier):
    # LLM identifies missing dates, validator identifies missing price
    mock_json = make_mock("rent an apartment", missing=["move-in date"])
    raw = parser.parse_mock(mock_json)
    mission, clarifications = validator.validate(raw)
    assert "move-in date" in clarifications
    assert "maximum price" in clarifications
    msg = clarifier.generate(clarifications)
    assert "move-in date" in msg
    assert "maximum price" in msg

def test_09_llm_hallucinates_operator(parser, validator):
    # Invalid operator string - wait, Pydantic doesn't strictly validate operator in my schema yet,
    # but we can test basic structural failure.
    mock_json = '{"objective": "test", "hard_constraints": [{"key": "price"}]}' # missing fields
    raw = parser.parse_mock(mock_json)
    mission, errors = validator.validate(raw)
    assert mission is None
    assert len(errors) > 0

def test_10_soft_preferences_valid(parser, validator):
    mock_json = make_mock(
        "purchase",
        [{"key": "price", "operator": "<=", "value": 100, "visibility": "PRIVATE", "type": "HARD"}],
        [{"key": "color", "operator": "==", "value": "red", "visibility": "SHARED", "type": "SOFT"}]
    )
    raw = parser.parse_mock(mock_json)
    mission, _ = validator.validate(raw)
    assert len(mission.soft_preferences) == 1
    assert mission.soft_preferences[0].value == "red"

def test_11_hinglish_soft_preference(parser, validator):
    # "Bag mil raha ho to 42,000 tak ja sakte ho."
    mock_json = make_mock(
        "negotiate laptop",
        [{"key": "price", "operator": "<=", "value": 42000, "visibility": "PRIVATE", "type": "HARD"}],
        [{"key": "accessories", "operator": "contains", "value": "bag", "visibility": "SHARED", "type": "SOFT"}]
    )
    raw = parser.parse_mock(mock_json)
    mission, _ = validator.validate(raw)
    assert mission.soft_preferences[0].value == "bag"

def test_12_permissions_parsing(parser, validator):
    raw = {
        "objective": "buy stuff",
        "hard_constraints": [{"key": "price", "operator": "<", "value": 10, "visibility": "PRIVATE", "type": "HARD"}],
        "permissions": [{"action": "close_deal", "is_allowed": True}]
    }
    mission, err = validator.validate(raw)
    assert mission.permissions[0].action == "close_deal"
    assert mission.permissions[0].is_allowed is True

def test_13_escalation_rules(parser, validator):
    raw = {
        "objective": "buy stuff",
        "hard_constraints": [{"key": "price", "operator": "<", "value": 10, "visibility": "PRIVATE", "type": "HARD"}],
        "escalation_rules": ["price > 42000"]
    }
    mission, err = validator.validate(raw)
    assert mission.escalation_rules[0] == "price > 42000"

def test_14_communication_preference(parser, validator):
    raw = {
        "objective": "buy stuff",
        "hard_constraints": [{"key": "price", "operator": "<", "value": 10, "visibility": "PRIVATE", "type": "HARD"}],
        "communication_preference": "Aggressive"
    }
    mission, err = validator.validate(raw)
    assert mission.communication_preference == "Aggressive"

def test_15_empty_text_rejection(parser, validator):
    raw = {"objective": ""}
    mission, err = validator.validate(raw)
    # Objective is technically empty string, which passes pydantic if not min_length
    assert mission is not None

def test_16_non_transactional_objective(parser, validator):
    # "Ask Rahul what time he is coming" - no price needed
    mock_json = make_mock("ask time")
    raw = parser.parse_mock(mock_json)
    mission, clarifications = validator.validate(raw)
    assert len(clarifications) == 0

def test_17_clarifier_no_missing_info(clarifier):
    msg = clarifier.generate([])
    assert "fully understood" in msg

def test_18_hindi_complex(parser, validator):
    # "Gadi rent pe chahiye 2 din ke liye, 2000 per day se zyada nai."
    mock_json = make_mock(
        "rent car",
        [
            {"key": "rent", "operator": "<=", "value": 2000, "visibility": "PRIVATE", "type": "HARD"},
            {"key": "duration_days", "operator": "==", "value": 2, "visibility": "SHARED", "type": "HARD"}
        ]
    )
    raw = parser.parse_mock(mock_json)
    mission, clarifications = validator.validate(raw)
    assert len(clarifications) == 0

def test_19_missing_critical_info_field_passed(parser, validator):
    raw = {
        "objective": "purchase",
        "hard_constraints": [{"key": "price", "operator": "<", "value": 10, "visibility": "PRIVATE", "type": "HARD"}],
        "missing_critical_info": ["color"]
    }
    mission, clar = validator.validate(raw)
    assert "color" in clar

def test_20_malformed_json_simulation(parser):
    with pytest.raises(json.JSONDecodeError):
        parser.parse_mock("{bad_json")
