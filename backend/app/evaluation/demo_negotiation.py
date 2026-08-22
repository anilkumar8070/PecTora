import sys
import time
from app.evaluation.simulation_partner import SimulationPartner, Personality
from app.evaluation.schemas import SimState
from app.negotiation.schemas import NegotiationState, LLMRecommendation
from app.missions.schemas import ExtractedMission, ConstraintSchema, PermissionSchema
from app.negotiation.engine import NegotiationEngine
from app.communication.fake_channel import FakeChannel

class DeterministicMockAgent:
    """A deterministic AI Provider mock that haggles towards a target price."""
    def __init__(self, target_price: float, max_price: float):
        self.target_price = target_price
        self.max_price = max_price
        self.current_offer = target_price * 0.9 # Start a bit low

    def get_recommendation(self, incoming_text: str, incoming_price: float) -> LLMRecommendation:
        if incoming_price <= self.max_price:
            return LLMRecommendation(
                intent="ACCEPT",
                dialogue=f"I agree to {incoming_price}.",
                proposed_offer={"price": incoming_price}
            )
            
        # Haggle up slowly
        self.current_offer += (self.max_price - self.current_offer) * 0.3
        self.current_offer = round(self.current_offer)
        
        if self.current_offer > self.max_price:
            self.current_offer = self.max_price
            
        return LLMRecommendation(
            intent="COUNTER",
            dialogue=f"I can offer {self.current_offer}.",
            proposed_offer={"price": self.current_offer}
        )

def main():
    print("="*50)
    print("Pectora EVALUATION DEMO")
    print("="*50)
    
    # Seller Configuration
    seller = SimulationPartner(
        role="Seller", 
        starting_price=47000, 
        minimum_price=40500, 
        personality=Personality.RATIONAL,
        seed=123
    )
    
    # Agent Configuration
    mission = ExtractedMission(
        objective="Buy laptop",
        hard_constraints=[
            ConstraintSchema(key="price", operator="<=", value=42000, visibility="PRIVATE", type="HARD")
        ],
        permissions=[
            PermissionSchema(action="close_deal", is_allowed=True),
            PermissionSchema(action="make_offers", is_allowed=True)
        ]
    )
    
    channel = FakeChannel()
    engine = NegotiationEngine(mission, channel)
    agent = DeterministicMockAgent(target_price=40000, max_price=42000)

    # 1. Seller opens
    seller_msg, seller_offer = seller.generate_opening()
    print(f"\n[Seller]: {seller_msg}")
    
    turn = 1
    while engine.state not in [NegotiationState.AGREED, NegotiationState.WALKED_AWAY, NegotiationState.FAILED]:
        time.sleep(1) # For demo pacing
        
        # 2. Agent processes seller's message
        # Since we use a dynamic mock agent here, we generate the recommendation on the fly 
        # and inject it into the engine's mock list.
        rec = agent.get_recommendation(seller_msg, seller_offer["price"])
        engine.llm_mock = [rec]
        
        # The engine processes the incoming message, asks the mock LLM, runs the firewall, and outputs.
        # Format the incoming message so the engine's simplistic parser sees it
        formatted_incoming = f"{seller_msg} offer: {seller_offer['price']}"
        engine.process_turn(formatted_incoming)
        
        agent_msg = channel.sent_messages.pop(0) if channel.sent_messages else None
        if not agent_msg:
            print("[System]: Communication failed.")
            break
            
        print(f"\n[Agent]: {agent_msg}")
        
        if engine.state == NegotiationState.AGREED:
            print("\n>>> FINAL: AGREEMENT REACHED <<<")
            break
        elif engine.state in [NegotiationState.WALKED_AWAY, NegotiationState.FAILED]:
            print(f"\n>>> FINAL: {engine.state.value} <<<")
            break
            
        # 3. Seller processes Agent's offer
        # Extract the agent's offer from engine history
        agent_offer_val = rec.proposed_offer["price"] if rec.proposed_offer else 0
        seller_msg, seller_offer, intent = seller.process_offer(agent_offer_val)
        
        time.sleep(1)
        print(f"\n[Seller]: {seller_msg}")
        
        if intent == "ACCEPT":
            print("\n>>> FINAL: AGREEMENT REACHED <<<")
            break
            
        turn += 1
        if turn > 10:
            print("\n>>> FINAL: DEADLOCK (Max Turns) <<<")
            break

if __name__ == "__main__":
    main()
