import openai

from clients.base_client import Client

from openai import OpenAI
from config import load_configuration

config = load_configuration()

client = OpenAI(base_url = "https://integrate.api.nvidia.com/v1", api_key=config['NVIDIA_API_KEY'])

class OpenAIClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)
        openai.api_base = "https://integrate.api.nvidia.com/v1"  # NVIDIA API base URL
        openai.api_key = api_key

    def generate_text(self, prompt, **kwargs):
        response = client.chat.completions.create(
            # model="meta/llama3-70b-instruct",  # or the model you want to use
            messages=[{"role": "user", "content": prompt}],
            # temperature=0.5,
            # top_p=1,
            # max_tokens=4000,
            **kwargs
        )
        return response.choices[0].message.content.strip()