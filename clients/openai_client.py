import openai

from clients.base_client import Client


class OpenAIClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)
        openai.api_key = api_key

    def generate_text(self, prompt, **kwargs):
        response = openai.Completion.create(
            model="meta/llama3-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.5,
            top_p=1,
            **kwargs
        )
        return response.choices[0].text.strip()
