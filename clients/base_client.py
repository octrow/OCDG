from .openai_client import OpenAIClient
from .groq_client import GroqClient
from .replicate_client import ReplicateClient
from abc import ABC, abstractmethod

class Client(ABC):
    def __init__(self, api_key):
        self.api_key = api_key

    @abstractmethod
    def generate_text(self, prompt, **kwargs):
        pass


def create_client(client_type, api_key):
    clients = {
        "openai": OpenAIClient,
        "groq": GroqClient,
        "replicate": ReplicateClient
    }
    return clients[client_type](api_key)