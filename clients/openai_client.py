import os
import openai

from clients.base_client import Client

from openai import OpenAI, AsyncOpenAI
from loguru import logger
from retry_utils import retry_with_backoff


class OpenAIClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)
        nvidia_key = os.getenv('NVIDIA_API_KEY', api_key)
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",  # NVIDIA API base URL
            api_key=nvidia_key,
            timeout=10,  # Set a timeout (in seconds)
        )
        self.async_client = AsyncOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_key,
            timeout=10,
        )
        self.model = "meta/llama3-70b-instruct"  # Default model

    @retry_with_backoff(max_retries=3, exceptions=(openai.APIError, openai.RateLimitError, openai.APIConnectionError))
    def generate_text(self, prompt, **kwargs):
        logger.info(f"Sending request to OpenAI API (model: {self.model})...")
        logger.debug(f"Prompt: {prompt}")
        logger.debug(f"Additional parameters: {kwargs}")
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        logger.info("OpenAI API response received.")
        logger.debug(f"Full response: {response}")
        text_content = response.choices[0].message.content.strip()
        logger.debug(f"Generated text: {text_content[:50]}...")
        return text_content

    @retry_with_backoff(max_retries=3, exceptions=(openai.APIError, openai.RateLimitError, openai.APIConnectionError))
    async def async_generate_text(self, system_prompt, prompt, **kwargs):
        logger.info(f"Sending async request to OpenAI API (model: {self.model})...")
        logger.debug(f"Prompt: {prompt}")
        logger.debug(f"Additional parameters: {kwargs}")
        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            **kwargs
        )
        logger.info("OpenAI API async response received.")
        logger.debug(f"Full response: {response}")
        text_content = response.choices[0].message.content.strip()
        logger.debug(f"Generated text: {text_content[:50]}...")
        return text_content