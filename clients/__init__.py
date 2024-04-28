from .openai_client import OpenAIClient
from .groq_client import GroqClient
from .replicate_client import ReplicateClient
from .base_client import Client

def create_client(client_type):
    clients = {
        "openai": OpenAIClient,
        "groq": GroqClient,
        "replicate": ReplicateClient
    }
    return clients[client_type]
