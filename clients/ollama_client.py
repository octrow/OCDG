import ollama

from clients.base_client import Client

from ollama import Client as OllClient
from config import load_configuration
from loguru import logger
config = load_configuration()


class OllamaClient(Client):
    def __init__(self, api_key='ollama'):
        super().__init__(api_key)
        self.host = 'http://localhost:11434'
        self.timeout = 30
        self.client = OllClient(
            host=self.host,
            timeout=self.timeout,  # Set a timeout (in seconds)
        )
        self.async_client = ollama.AsyncClient(  # Use AsyncClient
            host=self.host,
            timeout=self.timeout,
        )
        self.model = 'llama3'

    async def async_generate_text(self, prompt, **kwargs):  # Make generate_text asynchronous
        try:
            logger.info(f"Sending request to Ollama API (model: {self.model})...")
            logger.debug(f"Prompt: {prompt}")
            logger.debug(f"Additional parameters: {kwargs}")

            response = await self.async_client.chat(  # Use await
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format='json',
                **kwargs
            )
            logger.info("Ollama API response received.")
            logger.debug(f"Full response: {response}")
            text_content = response['message']['content'].strip()
            logger.debug(f"Generated text: {text_content[:50]}...")
            return text_content

        except Exception as e:
            logger.error(f"Unexpected error during LLM Ollama API call: {e}")
            raise

    def generate_text(self, prompt, **kwargs):
        try:
            # Log the request parameters (prompt and other kwargs)
            logger.info(f"Sending request to Ollama API (model: {self.model})...")
            logger.debug(f"Prompt: {prompt}")
            logger.debug(f"Additional parameters: {kwargs}")
            response = self.client.chat(
                model=self.model,  # or the model you want to use
                messages=[{"role": "user", "content": prompt}],
                format='json',
                # temperature=0.5,
                # top_p=1,
                # max_tokens=4000,
                **kwargs
            )
            # Log the raw response from the API
            logger.info("Ollama API response received.")
            logger.debug(f"Full response: {response}")  # Full response logged at DEBUG
            # Extract and return the text content
            text_content = response['message']['content'].strip()
            logger.debug(f"Generated text: {text_content[:50]}...")
            return text_content
        except ollama.ResponseError as e:
            # Handle API error here, e.g. retry or log
            print(f"Ollama API returned an ResponseError: {e}")
            raise
        except ollama.RequestError as e:
            print(f"Ollama API returned an RequestError: {e}")
            raise
        except Exception as e:
            # Log general exceptions
            logger.error(f"Unexpected error during LLM Ollama API call: {e}")
            raise