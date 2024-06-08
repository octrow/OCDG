
from abc import ABC, abstractmethod

class Client(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generates text using the LLM."""
        pass
