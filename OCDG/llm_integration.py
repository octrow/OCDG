import os
import traceback

from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
# from commit_message_generator import generate_commit_message_prefix

# Replace with your API key and model name
API_KEY = "YOUR_API_KEY"
MODEL_NAME = "meta/llama3-70b-instruct"

llm = ChatNVIDIA(model=MODEL_NAME, api_key=API_KEY)

def split_diff(diff, chunk_size=1500, chunk_overlap=200):
    """Splits a large diff into smaller chunks with overlap."""
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_text(diff)
    return chunks

def generate_prompt(diff_chunk, old_description, is_partial=False):
    """Generates a prompt for Llama 3 based on diff chunk and old description."""
    # prefix = generate_commit_message_prefix(old_description)
    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content="You are a helpful AI assistant that generates commit messages based on code changes and previous descriptions. Follow the commit guidelines of the GitHub repository."
            ),
            HumanMessage(content=f"Previous commit message: {old_description}"),
            HumanMessage(
                content=f"Code changes:{' (partial)' if is_partial else ''} \n```\n{diff_chunk}\n```"
            ),
            HumanMessage(content="Generate a new commit message based on these changes."),
        ]
    )
    prompt = prompt_template.format()
    return prompt

def generate_commit_description(history):
    """Generates a commit description for a potentially large diff."""
    logger.info(f'history.get_oldest_commit.diff: {history.get_oldest_commit().diff[:100]}')
    logger.info(f'history.get_oldest_commit.description: {history.get_oldest_commit().message}')
    logger.info(f'delete oldest_commit: {history.get_oldest_commit().delete()}')
    logger.info(f'history.get_oldest_commit.description: {history.get_oldest_commit().message}')
    diff, old_description = history
    if len(diff) <= 2000:
        # Diff is small enough, process directly
        prompt = generate_prompt(diff, old_description)
        new_description = llm.invoke(prompt).content
    else:
        # Split diff and process chunks
        chunks = split_diff(diff)
        partial_descriptions = []
        for i, chunk in enumerate(chunks):
            is_partial = i != len(chunks) - 1
            prompt = generate_prompt(chunk, old_description, is_partial)
            partial_description = llm.invoke(prompt).content
            partial_descriptions.append(partial_description)

        # Merge partial descriptions into final description
        merge_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content="You are a helpful AI assistant that merges partial commit messages into a final, comprehensive message."
                ),
                HumanMessage(content="Partial commit messages:"),
            ]
            + [HumanMessage(content=desc) for desc in partial_descriptions]
            + [HumanMessage(content="Merge these into a single commit message.")]
        )
        new_description = llm.invoke(merge_prompt).content
    return new_description
#############################################################################

# from openai import OpenAI
#
# class LLMInterface:
#     def __init__(self, api_key):
#         self.client = OpenAI(
#             base_url="https://integrate.api.nvidia.com/v1",
#             api_key=api_key,
#         )
#
#     def generate_commit_message(self, diff, old_message):
#         messages = [
#             {"role": "system", "content": "You are a helpful AI assistant for generating concise and informative Git commit messages."},
#             {"role": "user", "content": f"Here is the diff for a commit:\n{diff}\n\nThe old commit message was:\n{old_message}"},
#         ]
#
#         response = self.client.chat.completions.create(
#             model="meta/llama3-70b-instruct",
#             messages=messages,
#             temperature=0.5,  # Adjust temperature for creativity
#             max_tokens=2000,  # Adjust max tokens for message length
#             n=1,  # Get only one response
#             stop=None,  # Let the model decide where to stop
#         )
#         new_message = response.choices[0].message.content
#         logger.success(f"Generated new message: {new_message}")
#         return new_message

#########################################################################
# from langchain import PromptTemplate
# from langchain_nvidia_ai_endpoints import ChatNVIDIA
# from dotenv import load_dotenv
# load_dotenv()
#
# class LLMInterface:
#     def __init__(self):
#         self.api_key = os.getenv("NVIDIA_API_KEY")
#         self.llm = ChatNVIDIA(model="meta/llama3-70b-instruct")  # Initialize Llama 3
#         self.chunk_size = 1800  # Set chunk size below token limit
#         self.prompt_template = PromptTemplate(
#             input_variables=["diff", "old_message", "chunk_index", "total_chunks"],
#             template="""
#             ## Code Changes:
#             ```diff
#             {diff}
#             ```
#             ## Old Commit Message:
#             {old_message}
#
#             ## Instructions:
#             You are a helpful AI assistant for generating commit messages based on code changes and conventional guidelines.
#
#             {chunk_info}
#
#             Please provide a concise and informative commit message that accurately summarizes the changes in the code.
#             """
#         )
#
#     def generate_commit_message(self, diff, old_message, chunk_index=None, total_chunks=None):
#         logger.info(f"Generating commit message for chunk {chunk_index} of {total_chunks}..." if chunk_index is not None else "Generating commit message...")
#         try:
#             if chunk_index is not None:
#                 chunk_info = f"This is part {chunk_index + 1} of {total_chunks}."
#             else:
#                 chunk_info = ""
#
#             if len(diff) > self.chunk_size:
#                 # Split diff into chunks
#                 chunks = [diff[i:i + self.chunk_size] for i in range(0, len(diff), self.chunk_size)]
#                 responses = []
#                 for i, chunk in enumerate(chunks):
#                     prompt = self.prompt_template.format(
#                         diff=chunk,
#                         old_message=old_message,
#                         chunk_index=i,
#                         total_chunks=len(chunks),
#                         chunk_info=chunk_info)
#                     response = self.llm(prompt)
#                     responses.append(response.content)
#                     # Merge chunked responses
#                     merge_prompt = f"Combine these commit message parts into a single coherent commit message:\n\n" + "\n\n".join(responses)
#                 final_response = self.llm(merge_prompt)
#                 logger.success(f"Generated new message from chunks: {final_response.content}")
#                 return final_response.content
#             else:
#                 # Generate commit message directly
#                 prompt = self.prompt_template.format(
#                     diff=diff,
#                     old_message=old_message,
#                     chunk_index=None,
#                     total_chunks=None,
#                     chunk_info=chunk_info)
#                 response = self.llm(prompt)
#                 logger.success(f"Generated new message: {response.content}")
#                 return response.content
#         except Exception as e:
#             logger.error(f"Failed to generate commit message: {e}")
#             logger.error(f'traceback.format_exc(): {traceback.format_exc()}')
#             raise
#############################################################################
# from langchain_nvidia_ai_endpoints import ChatNVIDIA
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import ChatPromptTemplate
# from langchain.prompts import PromptTemplate
# from dotenv import load_dotenv
# load_dotenv()
#
# NVIDIANGC_API_KEY = os.getenv('NVIDIA_API_KEY')
#
# prompt = ChatPromptTemplate.from_messages(
#     [("system", "You are a helpful AI assistant named Fred."), ("user", "{input}")]
# )
# prompt_template = PromptTemplate(
#     input_variables=["diff", "old_message"],
#     template="""
# ## Commit Message Generation
#
# **Diff:**
# ```diff
# {diff}
# ```
#
# **Old Message:**
# {old_message}
#
# **New Message (Conventional Commit format):**
# """,)
#
#
#
# for txt in chain.stream({"input": "What's your name?"}):
#     print(txt, end="")
#
# llm = ChatNVIDIA(model="meta/llama3-70b-instruct", client=)
# result = llm.invoke("Write a ballad about LangChain.")
# print(result.content)
#
#
# def generate_commit_message_lchng(diff, old_message):
#     prompt = prompt_template.format(diff=diff, old_message=old_message)
#     chain = prompt | ChatNVIDIA(model="meta/llama3-70b-instruct",
#                                 temperature=0.5,
#                                 top_p=1,
#                                 max_tokens=2000,
#                                 seed=0) | StrOutputParser()
#     new_message = response.choices[0].message.content
#     logger.success(f"Generated new message: {new_message}")
#     return new_message