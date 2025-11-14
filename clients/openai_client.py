import os
import openai

from clients.base_client import Client

from openai import OpenAI, AsyncOpenAI
from loguru import logger


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

    def generate_text(self, prompt, **kwargs):
        try:
            # Log the request parameters (prompt and other kwargs)
            logger.info(f"Sending request to OpenAI API (model: {self.model})...")
            logger.debug(f"Prompt: {prompt}")
            logger.debug(f"Additional parameters: {kwargs}")
            response = self.client.chat.completions.create(
                # model="meta/llama3-70b-instruct",  # or the model you want to use
                messages=[{"role": "user", "content": prompt}],
                # temperature=0.5,
                # top_p=1,
                # max_tokens=4000,
                **kwargs
            )
            # Log the raw response from the API
            logger.info("OpenAI API response received.")
            logger.debug(f"Full response: {response}")  # Full response logged at DEBUG
            # Extract and return the text content
            text_content = response.choices[0].message.content.strip()
            logger.debug(f"Generated text: {text_content[:50]}...")
            return text_content
        except openai.APIError as e:
            # Handle API error here, e.g. retry or log
            print(f"OpenAI API returned an API Error: {e}")
            raise
        except openai.RateLimitError as e:
            # Handle rate limit error (we recommend using exponential backoff)
            print(f"OpenAI API request exceeded rate limit: {e}")
            raise
        except Exception as e:
            # Log general exceptions
            logger.error(f"Unexpected error during LLM API call: {e}")
            raise

    async def async_generate_text(self, system_prompt, prompt, **kwargs):
        try:
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
        except openai.APIError as e:
            print(f"OpenAI API returned an API Error: {e}")
            raise
        except openai.RateLimitError as e:
            print(f"OpenAI API request exceeded rate limit: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during async LLM API call: {e}")
            raise