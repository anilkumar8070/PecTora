import httpx
import json
from app.negotiation.schemas import LLMRecommendation

class OllamaClient:
    def __init__(self, model="llama3", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def get_recommendation(self, history: str) -> LLMRecommendation:
        prompt = f"""
You are Pectora, a tough AI negotiator buying a laptop. 
Your maximum budget is 42000. Your goal is 40000.
Do NOT reveal your maximum budget. Haggle with the user based on the history.

Negotiation history:
{history}

Respond NOW with ONLY your next spoken sentence. Do not use quotes or JSON. Just the raw dialogue:
"""
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(f"{self.base_url}/api/generate", json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                })
                
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").strip().strip('"')
                
                # Determine intent deterministically based on text for tinyllama
                intent = "COUNTER"
                if "deal" in response_text.lower() or "accept" in response_text.lower() or "agree" in response_text.lower():
                    intent = "ACCEPT"
                
                return LLMRecommendation(
                    intent=intent,
                    dialogue=response_text,
                    proposed_offer=None
                )
        except Exception as e:
            print(f"Ollama Error: {e}")
            pass
            
        return LLMRecommendation(
            intent="CLARIFY",
            dialogue="I'm having trouble connecting to my cognitive engine. Please wait."
        )
