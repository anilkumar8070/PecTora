import pytest
from app.verification.engine import AgreementVerifier
from app.missions.schemas import ExtractedMission, ConstraintSchema, PermissionSchema

@pytest.fixture
def verifier():
    return AgreementVerifier()

@pytest.fixture
def base_mission():
    return ExtractedMission(
        objective="Buy laptop",
        hard_constraints=[
            ConstraintSchema(key="price", operator="<=", value=42000, visibility="PRIVATE", type="HARD"),
            ConstraintSchema(key="item", operator="==", value="laptop", visibility="SHARED", type="HARD"),
            ConstraintSchema(key="warranty", operator="contains", value="1 year", visibility="SHARED", type="HARD")
        ],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)],
        escalation_rules=["price > 40000"]
    )

def test_01_valid_agreement(verifier, base_mission):
    terms = {"price": 38000, "item": "laptop", "warranty": "1 year included"}
    res = verifier.verify(terms, base_mission)
    assert res.valid is True
    assert res.confidence == 1.0

def test_02_invalid_price_exceeds_max(verifier, base_mission):
    terms = {"price": 43000, "item": "laptop", "warranty": "1 year"}
    res = verifier.verify(terms, base_mission)
    assert res.valid is False
    assert any("price" in v and "<= 42000" in v for v in res.violations)

def test_03_missing_required_term(verifier, base_mission):
    terms = {"price": 40000, "item": "laptop"} # Missing warranty
    res = verifier.verify(terms, base_mission)
    assert res.valid is False
    assert "warranty" in res.missing_terms

def test_04_invalid_item_mismatch(verifier, base_mission):
    terms = {"price": 40000, "item": "desktop", "warranty": "1 year"}
    res = verifier.verify(terms, base_mission)
    assert res.valid is False
    assert any("item (desktop) must be == laptop" in v for v in res.violations)

def test_05_missing_close_deal_permission(verifier, base_mission):
    base_mission.permissions = []
    terms = {"price": 38000, "item": "laptop", "warranty": "1 year"}
    res = verifier.verify(terms, base_mission)
    assert res.valid is False
    assert res.requires_human is True
    assert any("Agent does not have explicit permission" in v for v in res.violations)

def test_06_ambiguous_term_tbd(verifier, base_mission):
    terms = {"price": 38000, "item": "laptop", "warranty": "TBD"}
    res = verifier.verify(terms, base_mission)
    assert res.valid is False
    assert res.requires_human is True
    assert res.confidence == 0.5
    assert any("Ambiguous term" in v for v in res.violations)

def test_07_ambiguous_term_maybe(verifier, base_mission):
    terms = {"price": 38000, "item": "laptop", "warranty": "Maybe 1 year"}
    res = verifier.verify(terms, base_mission)
    assert res.valid is False
    assert res.requires_human is True

def test_08_contradictory_price_terms(verifier, base_mission):
    terms = {"price": 38000, "total_cost": 40000, "item": "laptop", "warranty": "1 year"}
    res = verifier.verify(terms, base_mission)
    assert res.valid is False
    assert any("Contradiction: 'price' and 'total_cost' do not match" in v for v in res.violations)

def test_09_contradictory_dates(verifier, base_mission):
    terms = {"price": 38000, "item": "laptop", "warranty": "1 year", "start_date": "2026-12-01", "end_date": "2026-11-01"}
    res = verifier.verify(terms, base_mission)
    assert res.valid is False
    assert any("start_date' is after 'end_date'" in v for v in res.violations)

def test_10_escalation_rule_triggered(verifier, base_mission):
    # Rule is price > 40000
    terms = {"price": 41000, "item": "laptop", "warranty": "1 year"}
    res = verifier.verify(terms, base_mission)
    # Valid price for constraints (<=42000), but triggers escalation
    assert res.valid is False
    assert res.requires_human is True
    assert any("Escalation rule triggered" in v for v in res.violations)

def test_11_escalation_rule_not_triggered(verifier, base_mission):
    terms = {"price": 39000, "item": "laptop", "warranty": "1 year"}
    res = verifier.verify(terms, base_mission)
    assert res.valid is True
    assert res.requires_human is False

def test_12_type_coercion_string_to_int(verifier, base_mission):
    terms = {"price": "40000", "item": "laptop", "warranty": "1 year"}
    res = verifier.verify(terms, base_mission)
    assert res.valid is True

def test_13_type_coercion_int_to_string(verifier):
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[ConstraintSchema(key="quantity", operator="==", value="5", visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"quantity": 5}, m)
    assert res.valid is True

def test_14_contains_operator_success(verifier):
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[ConstraintSchema(key="extras", operator="contains", value="mouse", visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"extras": "keyboard and mouse"}, m)
    assert res.valid is True

def test_15_contains_operator_failure(verifier):
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[ConstraintSchema(key="extras", operator="contains", value="mouse", visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"extras": "keyboard only"}, m)
    assert res.valid is False

def test_16_not_contains_operator_success(verifier):
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[ConstraintSchema(key="condition", operator="not_contains", value="refurbished", visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"condition": "brand new"}, m)
    assert res.valid is True

def test_17_not_contains_operator_failure(verifier):
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[ConstraintSchema(key="condition", operator="not_contains", value="refurbished", visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"condition": "factory refurbished"}, m)
    assert res.valid is False

def test_18_not_exists_success(verifier):
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[ConstraintSchema(key="hidden_fee", operator="not_exists", value=None, visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"price": 10}, m)
    assert res.valid is True

def test_19_privacy_leak_in_agreement_terms(verifier):
    # A private strategy leaked into the agreement text
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[
            ConstraintSchema(key="price", operator="<=", value=10, visibility="SHARED", type="HARD"),
            ConstraintSchema(key="strategy", operator="==", value="secret_plan", visibility="PRIVATE", type="HARD")
        ],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"price": 9, "notes": "We used the secret_plan"}, m)
    assert res.valid is False
    assert any("Private parameter leak detected" in v for v in res.violations)

def test_20_greater_than_success(verifier):
    m = ExtractedMission(
        objective="Sell",
        hard_constraints=[ConstraintSchema(key="price", operator=">", value=10, visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"price": 11}, m)
    assert res.valid is True

def test_21_greater_than_failure(verifier):
    m = ExtractedMission(
        objective="Sell",
        hard_constraints=[ConstraintSchema(key="price", operator=">", value=10, visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"price": 10}, m)
    assert res.valid is False

def test_22_less_than_success(verifier):
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[ConstraintSchema(key="price", operator="<", value=10, visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"price": 9}, m)
    assert res.valid is True

def test_23_less_than_failure(verifier):
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[ConstraintSchema(key="price", operator="<", value=10, visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"price": 10}, m)
    assert res.valid is False

def test_24_not_equal_success(verifier):
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[ConstraintSchema(key="color", operator="!=", value="red", visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"color": "blue"}, m)
    assert res.valid is True

def test_25_not_equal_failure(verifier):
    m = ExtractedMission(
        objective="Buy",
        hard_constraints=[ConstraintSchema(key="color", operator="!=", value="red", visibility="SHARED", type="HARD")],
        permissions=[PermissionSchema(action="close_deal", is_allowed=True)]
    )
    res = verifier.verify({"color": "red"}, m)
    assert res.valid is False
