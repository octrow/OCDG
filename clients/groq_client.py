from groq import Groq, AsyncGroq
from clients.base_client import Client
from loguru import logger


class GroqClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.client = Groq(api_key=api_key)
        self.async_client = AsyncGroq(api_key=api_key)

    def generate_text(self, prompt, **kwargs):
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "system", "content": prompt}],
            **kwargs
        )
        return chat_completion.choices[0].message.content

    async def async_generate_text(self, system_prompt, prompt, **kwargs):
        try:
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
        except Exception as e:
            logger.error(f"Unexpected error during async Groq API call: {e}")
            raise