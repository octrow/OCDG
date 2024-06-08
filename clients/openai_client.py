import openai

from clients.base_client import Client

from openai import OpenAI
from config import load_configuration
import logging

config = load_configuration()
logger = logging.getLogger(__name__)  # Get the logger


class OpenAIClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",  # NVIDIA API base URL
            api_key=config['NVIDIA_API_KEY'],
            timeout=10,  # Set a timeout (in seconds)
        )
        self.model = "meta/llama3-70b-instruct"  # Default model

    def generate_text(self, prompt, **kwargs):
        try:
            # Log the request parameters (prompt and other kwargs)
            logging.info(f"Sending request to OpenAI API (model: {self.model})...")
            logging.debug(f"Prompt: {prompt}")
            logging.debug(f"Additional parameters: {kwargs}")
            response = self.client.chat.completions.create(
                # model="meta/llama3-70b-instruct",  # or the model you want to use
                messages=[{"role": "user", "content": prompt}],
                # temperature=0.5,
                # top_p=1,
                # max_tokens=4000,
                **kwargs
            )
            # Log the raw response from the API
            logging.info("OpenAI API response received.")
            logging.debug(f"Full response: {response}")  # Full response logged at DEBUG
            # Extract and return the text content
            text_content = response.choices[0].message.content.strip()
            logging.debug(f"Generated text: {text_content[:50]}...")
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
            logging.error(f"Unexpected error during LLM API call: {e}")
            raise