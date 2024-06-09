from .openai_client import OpenAIClient
from .groq_client import GroqClient
from .replicate_client import ReplicateClient
from .ollama_client import OllamaClient
from .base_client import Client

def create_client(client_type: str, config: dict) -> Client:
    """Creates and returns an instance of the specified client type."""
    clients = {
        "openai": lambda: OpenAIClient(config.get('NVIDIA_API_KEY')),
        "groq": lambda: GroqClient(config.get('GROQ_API_KEY')),
        "replicate": lambda: ReplicateClient(config.get('REPLICATE_API_KEY')),  # Add REPLICATE_API_KEY to config
        "ollama": lambda: OllamaClient()
    }
    if client_type not in clients:
        raise ValueError(f"Invalid client type: {client_type}")
    return clients[client_type]()
