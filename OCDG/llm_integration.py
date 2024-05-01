# from langchain_community.llms import OpenAI
import os

import requests
from langchain_core.language_models import LLM
# from langchain.llms.base import LLM
# from langchain_openai import OpenAI
from openai import OpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')

prompt_template = PromptTemplate(
    input_variables=["diff", "old_message"],
    template="""
## Commit Message Generation

**Diff:**
```diff
{diff}
```

**Old Message:**
{old_message}

**New Message (Conventional Commit format):**
""",)

client = OpenAI()

completion = client.chat.completions.create(
    model="meta/llama3-70b",
    max_tokens=4000,
    stream=False,
    temperature=0.5,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    seed=0,
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ]
)

print(completion.choices[0].message)
class NvidiaLLM(LLM):

    @property
    def _llm_type(self):
        return "nvidia_llama3"

    def _call(self, prompt, stop=None, run_manager=None, **kwargs):
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {NVIDIA_API_KEY}"
        }
        payload = {
            "model": "meta/llama3-70b",
            "messages": [{"role": "user", "content": prompt}],
            # Add other parameters as needed
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise
        return response.json()["choices"][0]["message"]["content"]

    def _identifying_params(self):
        return {"model_name": "meta/llama3-70b"}



    def generate_commit_message(self, diff, old_message):
        """Generates a new commit message using the LLM."""
        prompt = prompt_template.format(diff=diff, old_message=old_message)
        # completion = self.llm.chat.completions.create(
        #     model="meta/llama3-70b-instruct",
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=0.5,
        #     top_p=1,
        #     max_tokens=1024,
        #     stream=True
        # )
        # new_message = ""
        # for chunk in completion:
        #     if chunk.choices[0].delta.content is not None:
        #         new_message += chunk.choices[0].delta.content
        try:
            new_message = self._call(prompt)
        except Exception as e:
            logger.error(f"Error generating commit message: {e}")
            raise
        logger.success(f"Generated new commit message: {new_message}")
        return new_message.strip()

# class LLMInterface:
#     """Handles interaction with the chosen Large Language Model using LangChain."""
#
#     def __init__(self, llm_type, **kwargs):
#         """Initializes the LLM based on the provided type and settings."""
#         if llm_type == "openai":
#             self.llm = OpenAI(
#                 base_url="https://integrate.api.nvidia.com/v1",
#                 api_key=NVIDIA_API_KEY  # replace with your actual OpenAI API key
#             ) # Add elif conditions for other LLMs (Llama3, Gemini) with their respective initialization
#         else:
#             raise ValueError(f"Unsupported LLM type: {llm_type}")

    # def generate_commit_message(self, diff, old_message):
    #     """Generates a new commit message using the LLM."""
    #     prompt = self.prompt_template.format(diff=diff, old_message=old_message)
    #     # completion = self.llm.chat.completions.create(
    #     #     model="meta/llama3-70b-instruct",
    #     #     messages=[{"role": "user", "content": prompt}],
    #     #     temperature=0.5,
    #     #     top_p=1,
    #     #     max_tokens=1024,
    #     #     stream=True
    #     # )
    #     # new_message = ""
    #     # for chunk in completion:
    #     #     if chunk.choices[0].delta.content is not None:
    #     #         new_message += chunk.choices[0].delta.content
    #     new_message = self.llm(prompt)
    #     logger.success(f"Generated new commit message: {new_message}")
    #     return new_message.strip()