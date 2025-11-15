from groq import Groq, AsyncGroq
from clients.base_client import Client
from loguru import logger
from retry_utils import retry_with_backoff


class GroqClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.client = Groq(api_key=api_key)
        self.async_client = AsyncGroq(api_key=api_key)

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def generate_text(self, prompt, **kwargs):
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "system", "content": prompt}],
            **kwargs
        )
        return chat_completion.choices[0].message.content

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    async def async_generate_text(self, system_prompt, prompt, **kwargs):
        logger.info("Sending async request to Groq API...")
        logger.debug(f"Prompt: {prompt}")
        logger.debug(f"Additional parameters: {kwargs}")
        chat_completion = await self.async_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            **kwargs
        )
        logger.info("Groq API async response received.")
        text_content = chat_completion.choices[0].message.content.strip()
        logger.debug(f"Generated text: {text_content[:50]}...")
        return text_content