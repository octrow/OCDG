import replicate
from clients.base_client import Client
from loguru import logger


class ReplicateClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.client = replicate.Client(api_token=api_key)

    def generate_text(self, prompt, **kwargs):
        try:
            logger.info("Sending request to Replicate API...")
            logger.debug(f"Prompt: {prompt}")
            model = kwargs.pop('model', 'meta/llama-2-70b-chat')
            input_params = {
                "prompt": prompt,
                **kwargs
            }
            output = self.client.run(model, input=input_params)
            text_content = "".join(output).strip()
            logger.info("Replicate API response received.")
            logger.debug(f"Generated text: {text_content[:50]}...")
            return text_content
        except Exception as e:
            logger.error(f"Unexpected error during Replicate API call: {e}")
            raise

    async def async_generate_text(self, system_prompt, prompt, **kwargs):
        try:
            logger.info("Sending async request to Replicate API...")
            logger.debug(f"Prompt: {prompt}")
            model = kwargs.pop('model', 'meta/llama-2-70b-chat')
            input_params = {
                "system_prompt": system_prompt,
                "prompt": prompt,
                **kwargs
            }
            output = await self.client.async_run(model, input=input_params)
            text_content = "".join(output).strip()
            logger.info("Replicate API async response received.")
            logger.debug(f"Generated text: {text_content[:50]}...")
            return text_content
        except Exception as e:
            logger.error(f"Unexpected error during async Replicate API call: {e}")
            raise