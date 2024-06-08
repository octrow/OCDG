from groq import Groq
from clients.base_client import Client


class GroqClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.client = Groq(api_key=api_key)

    def generate_text(self, prompt, **kwargs):
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "system", "content": prompt}],
            **kwargs
        )
        return chat_completion.choices[0].message.content