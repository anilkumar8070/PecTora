import random
from typing import Dict, Any, Tuple
from app.evaluation.schemas import Personality, SimState

class SimulationPartner:
    def __init__(self, role: str, starting_price: float, minimum_price: float, personality: Personality, seed: int = 42):
        self.role = role
        self.personality = personality
        self.state = SimState(
            starting_price=starting_price,
            minimum_price=minimum_price,
            current_offer=starting_price
        )
        # We use a localized Random instance to guarantee deterministic tests
        self.rng = random.Random(seed)
        
    def generate_opening(self) -> Tuple[str, Dict[str, Any]]:
        self.state.turn_count += 1
        msg = f"Hi, I am selling this for {self.state.starting_price}."
        return msg, {"price": self.state.starting_price}

    def process_offer(self, buyer_offer: float) -> Tuple[str, Dict[str, Any], str]:
        """
        Returns (dialogue, proposed_terms, intent)
        intent can be "ACCEPT", "COUNTER", "REJECT"
        """
        self.state.turn_count += 1
        
        # If the buyer offers at or above our current asking price (or starting price), accept.
        if buyer_offer >= self.state.current_offer:
            return "That works for me. We have a deal.", {"price": buyer_offer}, "ACCEPT"
            
        # If buyer offer is very low, based on personality they might reject or counter
        gap = self.state.current_offer - buyer_offer
        
        if self.personality == Personality.AGGRESSIVE:
            concession_rate = self.rng.uniform(0.05, 0.15)
        elif self.personality == Personality.FRIENDLY:
            concession_rate = self.rng.uniform(0.3, 0.5)
        elif self.personality == Personality.DIFFICULT:
            concession_rate = self.rng.uniform(0.0, 0.1)
        elif self.personality == Personality.INDECISIVE:
            concession_rate = self.rng.uniform(0.1, 0.6)
        else: # RATIONAL
            concession_rate = 0.25

        # Calculate new counteroffer
        drop_amount = gap * concession_rate
        new_offer = self.state.current_offer - drop_amount
        
        # Floor it to the absolute minimum price
        if new_offer < self.state.minimum_price:
            new_offer = self.state.minimum_price
            
        new_offer = round(new_offer)
        
        # Deadlock check
        if new_offer == self.state.current_offer and buyer_offer < self.state.minimum_price:
            # We refuse to go lower.
            return f"I cannot go any lower than {new_offer}. Take it or leave it.", {"price": new_offer}, "COUNTER"
            
        self.state.current_offer = new_offer
        
        # Generate dialogue based on personality
        if self.personality == Personality.FRIENDLY:
            dialogue = f"I want to make this work. How about we meet at {new_offer}?"
        elif self.personality == Personality.AGGRESSIVE:
            dialogue = f"Your offer is too low. My price is {new_offer} and that's final."
        elif self.personality == Personality.DIFFICULT:
            dialogue = f"No. I can do {new_offer}."
        elif self.personality == Personality.INDECISIVE:
            dialogue = f"I'm not sure... I guess I could do {new_offer}?"
        else:
            dialogue = f"Based on the market value, I counter with {new_offer}."
            
        return dialogue, {"price": new_offer}, "COUNTER"
