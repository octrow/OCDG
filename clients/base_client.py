
from abc import ABC, abstractmethod

class Client(ABC):
    def __init__(self, api_key):
        self.api_key = api_key

    @abstractmethod
    def generate_text(self, prompt, **kwargs):
        pass

