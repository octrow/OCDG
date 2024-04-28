from clients.base_client import Client


class GroqClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)

    def generate_text(self, prompt, **kwargs):
        response = self.client.query(prompt, **kwargs)
        return response