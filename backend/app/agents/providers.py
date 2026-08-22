from abc import ABC, abstractmethod
import os
import httpx
import logging

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    @abstractmethod
    def generate_json(self, prompt: str) -> str:
        """Returns a string containing a JSON object from the LLM."""
        pass

class OllamaProvider(AIProvider):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("MODEL_NAME", "llama3.1:8b")
        
    def generate_json(self, prompt: str) -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"  # Enforces strict JSON output in Ollama
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "{}")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

class MockProvider(AIProvider):
    """Used for deterministic testing."""
    def __init__(self, mock_response: str):
        self.mock_response = mock_response
        self.last_prompt = None
        
    def generate_json(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.mock_response
