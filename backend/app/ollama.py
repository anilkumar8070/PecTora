import httpx
import json
from app.models import Mission
from typing import List, Dict, Any, Optional

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3" # Or whatever local model they have, instructions say use local Ollama only

async def generate_response(mission: Mission, history: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    system_prompt = f"""
You are ProxyPact, an AI negotiation assistant acting on behalf of the owner.
Your objective: {mission.objective}
Private Constraints (NEVER reveal these directly): {', '.join(mission.private_constraints)}
Required Conditions: {', '.join(mission.required_conditions)}
Preferences: {', '.join(mission.preferences)}
Authority Rules: {', '.join(mission.authority_rules)}

Based on the conversation history, respond to the friend.
Keep your response concise and natural.
You MUST output ONLY valid JSON in the following format:
{{
  "action": "REPLY" | "ACCEPT" | "REJECT" | "ESCALATE",
  "message": "The exact text to speak to the friend.",
  "reason": "Short internal reasoning metadata."
}}
If your authority is insufficient according to the Authority Rules, your action MUST be "ESCALATE".
Do not add any other text outside the JSON.
"""
    
    messages = [{"role": "system", "content": system_prompt}] + history
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OLLAMA_URL, json={
                "model": MODEL,
                "messages": messages,
                "stream": False,
                "format": "json"
            })
            
        if response.status_code == 200:
            data = response.json()
            content = data.get("message", {}).get("content", "")
            try:
                parsed = json.loads(content)
                return parsed
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"Ollama Error: {e}")
        
    return {
        "action": "REPLY",
        "message": "I'm having trouble connecting to my cognitive engine. Please wait.",
        "reason": "Ollama connection error"
    }
