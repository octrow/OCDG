import openai

from clients.base_client import Client

class OpenAIClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)
        openai.api_key = api_key

    def generate_text(self, prompt, **kwargs):
        response = openai.ChatCompletion.create(
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content.strip()