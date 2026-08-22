import json
from typing import List, Dict, Any, Optional
from app.negotiation.schemas import NegotiationState, NegotiationTurn, Offer, LLMRecommendation
from app.missions.schemas import ExtractedMission, ConstraintSchema
from app.permissions.firewall import PrivacyFirewall, PrivacyLeakException
from app.permissions.engine import PermissionEvaluator
from app.permissions.schemas import ActionRequest, PermissionRule, Condition

class NegotiationEngine:
    def __init__(self, mission: ExtractedMission, channel, llm_mock=None):
        self.state = NegotiationState.CREATED
        self.mission = mission
        self.channel = channel
        self.llm_mock = llm_mock
        self.firewall = PrivacyFirewall()
        self.evaluator = PermissionEvaluator()
        
        self.turns: List[NegotiationTurn] = []
        self.max_rounds = 5
        self.previous_offers: List[Dict[str, Any]] = []
        
        # Build rules from mission
        self.rules = self._build_rules_from_mission(mission)
        
        self.state = NegotiationState.READY

    def _build_rules_from_mission(self, mission: ExtractedMission) -> List[PermissionRule]:
        rules = []
        # Convert mission constraints and permissions into Engine Rules
        # For simplicity in this mock, we map the explicit permissions
        for p in mission.permissions:
            conds = []
            if p.action == "close_deal":
                # Ensure we only close if hard constraints are met
                for c in mission.hard_constraints:
                    conds.append(Condition(key=c.key, operator=c.operator, value=c.value))
            rules.append(PermissionRule(action=f"CAN_{p.action.upper()}", is_allowed=p.is_allowed, conditions=conds))
        return rules

    def process_turn(self, incoming_text: str):
        if self.state in [NegotiationState.AGREED, NegotiationState.WALKED_AWAY, NegotiationState.FAILED]:
            return
            
        self.state = NegotiationState.OFFER_RECEIVED
        turn_num = len(self.turns) + 1
        
        # 1. Receive & 2. Parse (Simulated extraction)
        # In real life, ask LLM what the user said
        extracted_incoming_offer = None
        if "offer" in incoming_text.lower():
            # mock extraction for deterministic testing
            parts = incoming_text.split(":")
            if len(parts) == 2:
                try:
                    val = float(parts[1].strip())
                    extracted_incoming_offer = {"price": val}
                except ValueError:
                    pass

        turn = NegotiationTurn(
            turn_number=turn_num, 
            sender="COUNTERPARTY", 
            raw_message=incoming_text,
            offer=Offer(terms=extracted_incoming_offer) if extracted_incoming_offer else None
        )
        self.turns.append(turn)

        # Timeout / Max rounds check
        if turn_num >= self.max_rounds * 2:
            self.state = NegotiationState.FAILED
            self.channel.send("System: Max rounds reached. Walk away.")
            return

        self.state = NegotiationState.OFFER_EVALUATION

        # 7. Ask LLM for response
        llm_rec = self._ask_llm(self.turns)
        
        # Deadlock / Repeated offer detection
        if llm_rec.proposed_offer and llm_rec.proposed_offer in self.previous_offers:
            # We are repeating ourselves. Deadlock.
            self.state = NegotiationState.WALKED_AWAY
            self.channel.send("We are deadlocked. I must walk away.")
            return

        # 6. Check permissions & validate response
        if llm_rec.intent == "ACCEPT":
            req = ActionRequest(action="CLOSE_DEAL", payload=llm_rec.proposed_offer or extracted_incoming_offer or {})
            auth = self.evaluator.evaluate(req, self.rules)
            if not auth.allowed:
                self.state = NegotiationState.REJECTED
                self.channel.send("System Block: Cannot accept, violates limits.")
                return
        
        if llm_rec.proposed_offer:
            req = ActionRequest(action="MAKE_OFFERS", payload=llm_rec.proposed_offer)
            # Evaluate constraints loosely (e.g., must be <= max)
            # Here we just rely on firewall to catch leaks, but evaluator checks if action allowed
            auth = self.evaluator.evaluate(req, self.rules)
            if not auth.allowed and "CAN_MAKE_OFFERS" in [r.action for r in self.rules]:
                self.state = NegotiationState.REJECTED
                self.channel.send("System Block: Offer violates permissions.")
                return

        # 10. Privacy Filter
        try:
            action_dict = {"dialogue": llm_rec.dialogue, "offer": llm_rec.proposed_offer or {}}
            self.firewall.filter_outgoing(action_dict, self.mission.hard_constraints)
        except PrivacyLeakException as e:
            self.state = NegotiationState.FAILED
            self.channel.send(f"System Block: Privacy Leak Detected. Aborting.")
            return

        # 11. Send response
        self.channel.send(llm_rec.dialogue)
        
        if llm_rec.proposed_offer:
            self.previous_offers.append(llm_rec.proposed_offer)

        # Update State
        if llm_rec.intent == "ACCEPT":
            self.state = NegotiationState.VERIFYING
            # 14. Verify Agreement
            # In real system, independent LLM/Rules confirm. Here deterministic.
            self.state = NegotiationState.AGREED
        elif llm_rec.intent == "WALK_AWAY":
            self.state = NegotiationState.WALKED_AWAY
        elif llm_rec.proposed_offer:
            self.state = NegotiationState.COUNTEROFFER
        else:
            self.state = NegotiationState.WAITING

    def _ask_llm(self, turns: List[NegotiationTurn]) -> LLMRecommendation:
        """Simulates LLM response logic based on deterministic mocks passed in init."""
        if self.llm_mock:
            # We pop the next recommended action from the mock list
            if isinstance(self.llm_mock, list) and len(self.llm_mock) > 0:
                return self.llm_mock.pop(0)
        
        # Default fallback behavior for testing
        return LLMRecommendation(intent="CLARIFY", dialogue="I need more info.")
