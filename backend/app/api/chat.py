from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
from app.negotiation.ollama_client import OllamaClient

router = APIRouter()

class ChatRequest(BaseModel):
    history: str

client = OllamaClient(model="tinyllama")

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    recommendation = client.get_recommendation(request.history)
    return {
        "intent": recommendation.intent,
        "dialogue": recommendation.dialogue,
        "proposed_offer": recommendation.proposed_offer
    }
